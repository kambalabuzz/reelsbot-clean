import asyncio
import gc
import json
import tempfile
import time
import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from urllib.parse import urlencode

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse, PlainTextResponse
from pydantic import BaseModel
from supabase import create_client
import os
import stripe
from openai import OpenAI
import base64
import requests
import httpx
from pathlib import Path
import sys
import re

# Ensure local imports resolve when running on Render
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

from video_engine import generate_video, generate_script, reassemble_video, assemble_video_local_sync

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

PRICES = {
    "hobby": os.environ.get("STRIPE_PRICE_HOBBY"),
    "daily": os.environ.get("STRIPE_PRICE_DAILY"),
    "pro": os.environ.get("STRIPE_PRICE_PRO"),
}
app = FastAPI(title="ReelsBot API")
client = None
openai_key = os.environ.get("OPENAI_API_KEY")
if openai_key:
    client = OpenAI(api_key=openai_key)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"[STARTUP] Warning: Supabase initialization failed: {e}")

GENERATION_LOCK = threading.Lock()


def _get_next_queued_episode() -> Optional[tuple[str, str, dict]]:
    if not supabase:
        return None
    try:
        queued = (
            supabase.table("episodes")
            .select("*")
            .eq("status", "queued")
            .order("created_at", desc=False)
            .limit(1)
            .execute()
        )
        if not queued.data:
            return None
        episode = queued.data[0]
        series_result = supabase.table("series").select("*").eq("id", episode.get("series_id")).execute()
        if not series_result.data:
            supabase.table("episodes").update({"status": "failed"}).eq("id", episode.get("id")).execute()
            return None
        return episode.get("id"), episode.get("topic"), series_result.data[0]
    except Exception as e:
        print(f"[queue] Failed to fetch queued episode: {e}")
        return None


def _safe_update_video(video_id: str, fields: dict):
    if not supabase:
        return None
    if "updated_at" not in fields:
        fields = {**fields, "updated_at": datetime.now(timezone.utc).isoformat()}
    pending = dict(fields)
    attempts = 0
    missing_column_re = re.compile(r"Could not find the '([^']+)' column")

    # Determine which table to update
    table_name = "videos"  # default to old table
    try:
        director_check = supabase.table("director_videos").select("id").eq("video_id", video_id).execute()
        if director_check.data:
            table_name = "director_videos"
    except:
        pass

    while True:
        try:
            return supabase.table(table_name).update(pending).eq("video_id", video_id).execute()
        except Exception as e:
            msg = str(e)
            match = missing_column_re.search(msg)
            if match:
                missing = match.group(1)
                if missing in pending:
                    pending.pop(missing, None)
                    attempts += 1
                    if attempts < 6 and pending:
                        continue
            if "assembly_reason" in msg or "updated_at" in msg:
                trimmed = {k: v for k, v in pending.items() if k not in ("assembly_reason", "updated_at")}
                return supabase.table(table_name).update(trimmed).eq("video_id", video_id).execute()
            raise


def _resolve_assembly_backend(modal_url: Optional[str]) -> str:
    backend = os.environ.get("ASSEMBLY_BACKEND", "queue").lower()
    if backend == "auto":
        if os.environ.get("ASSEMBLY_QUEUE_ENABLED", "true").lower() != "false":
            return "queue"
        if modal_url:
            return "modal"
        return "local"
    return backend


def _build_assembly_payload(
    video_id: str,
    image_urls: list,
    audio_url: Optional[str],
    script: dict,
    config: dict,
    bgm_url: Optional[str] = None,
) -> dict:
    beats = script.get("beats") or []
    return {
        "video_id": video_id,
        "image_urls": image_urls,
        "audio_url": audio_url,
        "beats": beats,
        "durations": [b.get("duration", 4) for b in beats],
        "include_captions": config.get("include_captions", True),
        "caption_style": config.get("caption_style", "red_highlight"),
        "motion_effect": config.get("motion_effect", "ken_burns"),
        "transition_style": config.get("transition_style", "random"),
        "color_grade": config.get("color_grade", "cinematic"),
        "bgm_url": bgm_url or config.get("bgm_url"),
        "words_per_line": config.get("words_per_line", 2),
    }


def enqueue_assembly_job(video_id: str, payload: dict, priority: int = 5, source_type: str = "director", source_id: Optional[str] = None) -> Optional[dict]:
    if not supabase:
        return None
    try:
        existing = (
            supabase.table("assembly_jobs")
            .select("*")
            .eq("video_id", video_id)
            .in_("status", ["pending", "retry", "running"])
            .execute()
        )
        if existing.data:
            return existing.data[0]

        # Get source_id from database if not provided
        if not source_id:
            table_name = "director_videos" if source_type == "director" else "episodes"
            try:
                source_result = supabase.table(table_name).select("id").eq("video_id", video_id).execute()
                if source_result.data:
                    source_id = source_result.data[0].get("id")
            except Exception as e:
                print(f"[queue] Warning: Could not fetch source_id from {table_name}: {e}")

        insert = supabase.table("assembly_jobs").insert({
            "video_id": video_id,
            "status": "pending",
            "priority": priority,
            "payload": payload,
            "source_type": source_type,
            "source_id": source_id,
        }).execute()
        if insert.data:
            return insert.data[0]
        return None
    except Exception as e:
        print(f"[queue] Failed to enqueue assembly job: {e}")
        return None


def _find_video_in_storage(video_id: str) -> Optional[str]:
    if not supabase or not video_id:
        return None
    try:
        files = supabase.storage.from_("videos").list(video_id)
        if any(item.get("name") == "video.mp4" for item in files or []):
            return supabase.storage.from_("videos").get_public_url(f"{video_id}/video.mp4")
    except Exception as e:
        print(f"Storage lookup error: {e}")
    return None


def _maybe_reconcile_video(record: dict) -> dict:
    if not record:
        return record
    if record.get("video_url"):
        return record
    if record.get("status") not in ("assembling", "assets_ready"):
        return record
    video_id = record.get("video_id")
    video_url = _find_video_in_storage(video_id)
    if not video_url:
        return record
    try:
        update = _safe_update_video(video_id, {
            "status": "completed",
            "video_url": video_url,
            "assembly_reason": None,
        })
        if update and update.data:
            return update.data[0]
    except Exception as e:
        print(f"Reconcile update error: {e}")
    return record


def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


ASSEMBLY_RETRY_COOLDOWN_SECONDS = 600


# Basic in-memory rate limiting per IP
RATE_LIMIT_REQUESTS = int(os.environ.get("RATE_LIMIT_REQUESTS", 60))
RATE_LIMIT_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW", 60))
request_log: dict[str, deque] = defaultdict(deque)

# ElevenLabs
ELEVEN_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
DEFAULT_ELEVEN_VOICE = os.environ.get("ELEVENLABS_DEFAULT_VOICE", "pNInz6obpgDQGcFmaJgB")  # Adam
VOICE_CACHE_TTL = int(os.environ.get("VOICE_CACHE_TTL", 900))
voice_cache = {"ts": 0.0, "voices": None}

# Voice preview rate limiting (separate from global to reduce 429s)
VOICE_LIMIT_REQUESTS = int(os.environ.get("VOICE_LIMIT_REQUESTS", 20))
VOICE_LIMIT_WINDOW = int(os.environ.get("VOICE_LIMIT_WINDOW", 60))
voice_request_log: dict[str, deque] = defaultdict(deque)
# Limit how many voices we ever return (avoid huge payloads)
VOICE_MAX_RETURN = int(os.environ.get("VOICE_MAX_RETURN", 12))


@app.on_event("startup")
async def startup_event():
    """Validate configuration on startup"""
    print("[STARTUP] ReelsBot API Starting...")
    
    missing_keys = []
    if not openai_key:
        missing_keys.append("OPENAI_API_KEY")
    if not SUPABASE_URL or not SUPABASE_KEY:
        missing_keys.append("SUPABASE_URL/KEY")
    if not ELEVEN_API_KEY:
        print("[WARNING] ELEVENLABS_API_KEY not configured - voice generation will use OpenAI only")
    
    if missing_keys:
        print(f"[WARNING] Missing critical env vars: {', '.join(missing_keys)}")
    else:
        print("[STARTUP] ✓ All critical configurations present")


def rate_limiter(request: Request):
    now = time.time()
    client_ip = request.client.host if request and request.client else "unknown"
    timestamps = request_log[client_ip]

    while timestamps and now - timestamps[0] > RATE_LIMIT_WINDOW:
        timestamps.popleft()

    if len(timestamps) >= RATE_LIMIT_REQUESTS:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please slow down.")

    timestamps.append(now)
    return True


def voice_rate_limiter(request: Request):
    now = time.time()
    client_ip = request.client.host if request and request.client else "unknown"
    timestamps = voice_request_log[client_ip]
    while timestamps and now - timestamps[0] > VOICE_LIMIT_WINDOW:
        timestamps.popleft()
    if len(timestamps) >= VOICE_LIMIT_REQUESTS:
        raise HTTPException(status_code=429, detail="Too many voice previews. Please slow down.")
    timestamps.append(now)
    return True


def run_async(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    finally:
        asyncio.set_event_loop(None)
        loop.close()


def parse_platforms(raw):
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            return {}
    return {}


def parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        cleaned = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def beats_for_duration(duration: Optional[str]) -> int:
    mapping = {
        "short": 6,
        "medium": 8,
        "long": 10,
        "extra_long": 12,
    }
    return mapping.get(duration or "", 8)


class SeriesCreate(BaseModel):
    name: str
    niche: str
    language: str = "en"
    voice: str = "adam"
    music_tracks: List[str] = []
    art_style: str = "comic"
    caption_style: str = "red_highlight"
    platforms: dict = {"tiktok": False, "instagram": False, "youtube": False}
    video_duration: str = "medium"
    post_frequency: str = "daily"
    post_time: str = "18:00"


class EpisodeCreate(BaseModel):
    series_id: str
    topic: str


class SocialAccount(BaseModel):
    provider: str
    access_token: str
    refresh_token: Optional[str] = None
    profile_name: Optional[str] = None
    profile_id: Optional[str] = None
    scopes: Optional[List[str]] = None


class ViralScoreRequest(BaseModel):
    script: str
    topic: Optional[str] = None


class SeriesPlanRequest(BaseModel):
    topic: str
    num_episodes: int = 7
    niche: Optional[str] = None


class CloneRequest(BaseModel):
    video_url: Optional[str] = None
    transcript: Optional[str] = None


class ApplyTemplateRequest(BaseModel):
    analysis: dict
    topic: str


class EpisodeStats(BaseModel):
    views: Optional[int] = None
    likes: Optional[int] = None
    shares: Optional[int] = None
    comments: Optional[int] = None
    platform: Optional[str] = None
    posted_at: Optional[str] = None
    thumbnail_url: Optional[str] = None


class VoicePreviewRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None


class VideoGenerateRequest(BaseModel):
    topic: str
    voice: str = "adam"
    art_style: str = "cinematic"
    niche: str = "entertainment"
    beats_count: int = 8
    include_captions: bool = True
    caption_style: str = "karaoke"
    motion_effect: str = "ken_burns"
    bgm_mode: str = "random"  # random | library | custom | none
    bgm_track_id: Optional[str] = None
    bgm_custom_url: Optional[str] = None
    assemble: bool = True


class AssemblyCallbackRequest(BaseModel):
    video_id: str
    status: Optional[str] = None
    progress: Optional[int] = None
    stage: Optional[str] = None
    eta_seconds: Optional[int] = None
    elapsed_seconds: Optional[int] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    video_url: Optional[str] = None
    log: Optional[str] = None
    reason: Optional[str] = None


def normalize_post_time(value: Optional[str]) -> tuple[int, int]:
    if not value:
        return 18, 0
    try:
        hour_str, minute_str = value.split(":")
        return int(hour_str), int(minute_str)
    except Exception:
        return 18, 0


def build_schedule_slots(now: datetime, post_time: Optional[str], frequency: Optional[str]) -> list[datetime]:
    hour, minute = normalize_post_time(post_time)
    base = datetime(now.year, now.month, now.day, hour, minute, tzinfo=timezone.utc)
    freq = (frequency or "manual").lower()
    if freq == "daily":
        return [base, base - timedelta(days=1)]
    if freq == "twice_daily":
        return [base - timedelta(hours=12), base, base + timedelta(hours=12)]
    if freq == "three_per_week":
        if now.weekday() in (0, 2, 4):  # Mon, Wed, Fri
            return [base]
        return []
    return []


def get_latest_episode(series_id: str) -> Optional[dict]:
    try:
        result = (
            supabase.table("episodes")
            .select("*")
            .eq("series_id", series_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error fetching latest episode for series {series_id}: {e}")
        return None


def is_series_due(series: dict, now: datetime) -> bool:
    freq = (series.get("post_frequency") or "manual").lower()
    if freq in ("manual", "", None):
        return False

    slots = build_schedule_slots(now, series.get("post_time"), freq)
    due_slot = max((slot for slot in slots if slot <= now), default=None)
    if not due_slot:
        return False

    latest = get_latest_episode(series.get("id", ""))
    if latest:
        status = (latest.get("status") or "").lower()
        if status in {"queued", "generating"}:
            return False
        last_created = parse_iso_datetime(latest.get("created_at"))
        if last_created and last_created >= due_slot:
            return False

    return True


def recent_episode_topics(series_id: str, limit: int = 10) -> set[str]:
    try:
        result = (
            supabase.table("episodes")
            .select("topic")
            .eq("series_id", series_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        topics = [row.get("topic", "") for row in (result.data or [])]
        return {t.strip().lower() for t in topics if t}
    except Exception as e:
        print(f"Error fetching recent topics for {series_id}: {e}")
        return set()


def pick_series_topic(series: dict) -> str:
    niche = (series.get("niche") or "general").strip()
    series_name = (series.get("name") or "").strip()
    used = recent_episode_topics(series.get("id", ""))

    try:
        trends = get_trends(niche)
        trending_topics = [t.get("topic", "") for t in trends.get("trending_topics", [])] if trends else []
        for topic in trending_topics:
            cleaned = topic.strip()
            if cleaned and cleaned.lower() not in used:
                return cleaned
    except Exception as e:
        print(f"Trend lookup failed for {niche}: {e}")

    if series_name:
        stamp = datetime.now(timezone.utc).strftime("%b %d")
        return f"{series_name} - {stamp}"

    stamp = datetime.now(timezone.utc).strftime("%b %d")
    return f"{niche.title()} story - {stamp}"


def enqueue_episode(series: dict, topic: str, background_tasks: BackgroundTasks) -> dict:
    data = {
        "series_id": series.get("id"),
        "topic": topic,
        "status": "queued",
    }
    result = supabase.table("episodes").insert(data).execute()
    episode = result.data[0]
    background_tasks.add_task(generate_video_task, episode.get("id"), topic, series)
    return episode


def seed_series_episode(series: dict):
    topic = pick_series_topic(series)
    data = {
        "series_id": series.get("id"),
        "topic": topic,
        "status": "queued",
    }
    result = supabase.table("episodes").insert(data).execute()
    episode = result.data[0] if result.data else None
    if episode:
        generate_video_task(episode.get("id"), topic, series)


@app.post("/api/checkout")
def create_checkout(plan: str, user_email: str = "customer@example.com"):
    if plan not in PRICES:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{"price": PRICES[plan], "quantity": 1}],
        mode="subscription",
        success_url="https://reelsbot-alpha.vercel.app/dashboard?success=true",
        cancel_url="https://reelsbot-alpha.vercel.app/dashboard/billing?canceled=true",
        customer_email=user_email,
    )
    return {"url": session.url}


@app.get("/")
def root():
    return {"status": "ok", "message": "ReelsBot API with Supabase", "version": "1.1"}


@app.get("/terms")
def terms_page():
    """Serve Terms of Service page as plain HTML string"""
    html_path = Path(__file__).parent / "templates" / "terms.html"
    if html_path.exists():
        content = html_path.read_text()
        return PlainTextResponse(content=content, media_type="text/html")
    return PlainTextResponse(content="<h1>Terms of Service</h1><p>Coming soon</p>", media_type="text/html")


@app.get("/privacy")
def privacy_page():
    """Serve Privacy Policy page as plain HTML string"""
    html_path = Path(__file__).parent / "templates" / "privacy.html"
    if html_path.exists():
        content = html_path.read_text()
        return PlainTextResponse(content=content, media_type="text/html")
    return PlainTextResponse(content="<h1>Privacy Policy</h1><p>Coming soon</p>", media_type="text/html")


@app.post("/api/series")
def create_series(series: SeriesCreate, background_tasks: BackgroundTasks):
    # Parse platforms dict into individual boolean columns
    platforms = series.platforms or {}

    data = {
        "user_id": "demo_user",
        "name": series.name,
        "niche": series.niche,
        "language": series.language,
        "voice": series.voice,
        "music_tracks": series.music_tracks,  # Saved as JSON array
        "art_style": series.art_style,
        "caption_style": series.caption_style,
        "video_duration": series.video_duration,
        "post_frequency": series.post_frequency,
        "post_time": series.post_time,
        # Parse platforms into individual columns
        "post_to_tiktok": platforms.get("tiktok", False),
        "post_to_youtube": platforms.get("youtube", False),
        "post_to_instagram": platforms.get("instagram", False),
    }
    result = supabase.table("series").insert(data).execute()
    created = result.data[0]
    background_tasks.add_task(seed_series_episode, created)
    return created


@app.get("/api/series")
def list_series():
    result = supabase.table("series").select("*").execute()
    return result.data


@app.get("/api/series/{series_id}")
def get_series(series_id: str):
    result = supabase.table("series").select("*").eq("id", series_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Series not found")
    return result.data[0]


@app.delete("/api/series/{series_id}")
def delete_series(series_id: str):
    supabase.table("series").delete().eq("id", series_id).execute()
    return {"status": "deleted"}


@app.post("/api/episodes")
def create_episode(episode: EpisodeCreate, background_tasks: BackgroundTasks):
    series = supabase.table("series").select("*").eq("id", episode.series_id).execute()
    if not series.data:
        raise HTTPException(status_code=404, detail="Series not found")
    s = series.data[0]

    data = {
        "series_id": episode.series_id,
        "topic": episode.topic,
        "status": "queued",
    }
    result = supabase.table("episodes").insert(data).execute()
    ep = result.data[0]

    background_tasks.add_task(generate_video_task, ep.get("id"), episode.topic, s)
    return ep


@app.get("/api/episodes")
def list_episodes(series_id: Optional[str] = None):
    query = supabase.table("episodes").select("*")
    if series_id:
        query = query.eq("series_id", series_id)
    return query.execute().data


@app.delete("/api/episodes/{episode_id}")
def delete_episode(episode_id: str):
    """
    Delete/cancel an episode.
    - If episode is pending or queued: just delete it
    - If episode is generating: mark as cancelled and try to stop background task
    - If episode is completed: delete episode and associated video
    """
    # Get episode info
    episode_result = supabase.table("episodes").select("*").eq("id", episode_id).execute()
    if not episode_result.data:
        raise HTTPException(status_code=404, detail="Episode not found")

    episode = episode_result.data[0]
    status = episode.get("status", "")

    # If generating, update status to cancelled (background task should check and stop)
    if status == "generating":
        supabase.table("episodes").update({"status": "cancelled"}).eq("id", episode_id).execute()

    # Delete the episode (cascade will handle related records)
    supabase.table("episodes").delete().eq("id", episode_id).execute()

    return {"status": "deleted", "was_generating": status == "generating"}


@app.post("/api/cron/series")
def cron_series(background_tasks: BackgroundTasks, request: Request):
    secret = os.environ.get("CRON_SECRET")
    if secret:
        provided = request.headers.get("x-cron-secret") or request.query_params.get("secret")
        if provided != secret:
            raise HTTPException(status_code=403, detail="Forbidden")

    now = datetime.now(timezone.utc)
    series_list = supabase.table("series").select("*").execute().data or []
    queued = []
    errors = []

    for series in series_list:
        try:
            if not is_series_due(series, now):
                continue
            topic = pick_series_topic(series)
            episode = enqueue_episode(series, topic, background_tasks)
            queued.append({
                "series_id": series.get("id"),
                "episode_id": episode.get("id"),
                "topic": topic,
            })
        except Exception as e:
            errors.append({"series_id": series.get("id"), "error": str(e)})

    return {"queued": queued, "count": len(queued), "errors": errors}


@app.get("/api/social-accounts")
def list_social_accounts(user_id: str = "demo_user"):
    try:
        result = supabase.table("social_accounts").select("*").eq("user_id", user_id).execute()
        return result.data
    except Exception as e:
        print(f"Error fetching social accounts: {e}")
        return []


@app.post("/api/social-accounts/connect")
def connect_social_account(provider: str, user_id: str = "demo_user"):
    token_env = f"APIS_{provider.upper()}_TOKEN"
    placeholder_token = os.environ.get(token_env, f"demo-{provider}-token")
    try:
        data = {
          "user_id": user_id,
          "provider": provider,
          "access_token": placeholder_token,
          "refresh_token": None,
          "profile_name": f"{provider.title()} Account",
          "profile_id": f"{provider}_demo",
          "scopes": [],
        }
        result = supabase.table("social_accounts").upsert(data).execute()
        return result.data[0] if result.data else data
    except Exception as e:
        print(f"Error connecting social account: {e}")
        raise HTTPException(status_code=500, detail="Failed to connect account")


def youtube_redirect_uri(request: Request) -> str:
    return os.environ.get("GOOGLE_REDIRECT_URI") or f"{str(request.base_url).rstrip('/')}/api/auth/youtube/callback"


def encode_oauth_state(payload: dict) -> str:
    raw = json.dumps(payload).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def decode_oauth_state(state: Optional[str]) -> dict:
    if not state:
        return {}
    try:
        raw = base64.urlsafe_b64decode(state.encode("utf-8"))
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return {}


def append_query(url: str, key: str, value: str) -> str:
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}{key}={value}"


@app.get("/api/auth/{provider}/start")
def start_oauth(provider: str, request: Request, redirect_url: Optional[str] = None, user_id: str = "demo_user"):
    provider = provider.lower()

    if provider == "youtube":
        client_id = os.environ.get("GOOGLE_CLIENT_ID")
        if not client_id:
            raise HTTPException(status_code=400, detail="GOOGLE_CLIENT_ID not configured")

        redirect_uri = youtube_redirect_uri(request)
        state = encode_oauth_state({
            "redirect": redirect_url,
            "user_id": user_id,
        })
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly",
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true",
            "state": state,
        }
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        return {"auth_url": auth_url}

    elif provider == "tiktok":
        return start_tiktok_oauth(request, redirect_url, user_id)

    elif provider == "instagram":
        return start_instagram_oauth(request, redirect_url, user_id)

    else:
        # Generic fallback for other providers
        client_id_env = f"APIS_{provider.upper()}_CLIENT_ID"
        client_id = os.environ.get(client_id_env, f"demo-{provider}-client")
        auth_url = f"https://auth.{provider}.com/authorize?client_id={client_id}&redirect_uri={redirect_url}&response_type=code&state=demo"
        return {"auth_url": auth_url}


@app.get("/api/auth/youtube/callback")
def youtube_oauth_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
):
    payload = decode_oauth_state(state)
    redirect_target = payload.get("redirect") or os.environ.get("FRONTEND_URL") or "http://localhost:3000/dashboard/series/create"

    if error:
        return RedirectResponse(append_query(redirect_target, "error", error))
    if not code:
        return RedirectResponse(append_query(redirect_target, "error", "missing_code"))

    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    if not client_id or not client_secret:
        return RedirectResponse(append_query(redirect_target, "error", "missing_client"))

    redirect_uri = youtube_redirect_uri(request)
    token_resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=20,
    )
    if token_resp.status_code != 200:
        return RedirectResponse(append_query(redirect_target, "error", "token_exchange_failed"))

    token_data = token_resp.json()
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    scopes = token_data.get("scope", "").split()
    if not access_token:
        return RedirectResponse(append_query(redirect_target, "error", "missing_access_token"))

    profile_name = "YouTube"
    profile_id = "youtube"
    try:
        profile_resp = requests.get(
            "https://www.googleapis.com/youtube/v3/channels",
            params={"part": "snippet", "mine": "true"},
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15,
        )
        if profile_resp.status_code == 200:
            items = profile_resp.json().get("items", [])
            if items:
                profile_id = items[0].get("id", profile_id)
                profile_name = items[0].get("snippet", {}).get("title", profile_name)
    except Exception as e:
        print(f"YouTube profile fetch failed: {e}")

    user_id = payload.get("user_id", "demo_user")
    existing = (
        supabase.table("social_accounts")
        .select("*")
        .eq("user_id", user_id)
        .eq("provider", "youtube")
        .execute()
    )
    if existing.data and not refresh_token:
        refresh_token = existing.data[0].get("refresh_token")

    data = {
        "user_id": user_id,
        "provider": "youtube",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "profile_name": profile_name,
        "profile_id": profile_id,
        "scopes": scopes,
    }
    supabase.table("social_accounts").upsert(data).execute()

    return RedirectResponse(append_query(redirect_target, "connected", "youtube"))


def refresh_google_access_token(refresh_token: str) -> Optional[str]:
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None
    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=15,
    )
    if resp.status_code != 200:
        return None
    return resp.json().get("access_token")


def download_video_to_temp(video_url: str) -> Path:
    resp = requests.get(video_url, stream=True, timeout=60)
    resp.raise_for_status()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    with tmp as handle:
        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            if chunk:
                handle.write(chunk)
    return Path(tmp.name)


def youtube_upload_file(
    access_token: str,
    file_path: Path,
    title: str,
    description: str,
    tags: Optional[List[str]] = None,
) -> dict:
    file_size = file_path.stat().st_size
    tags = tags or []
    if "Shorts" not in tags:
        tags.append("Shorts")

    metadata = {
        "snippet": {
            "title": title[:100],
            "description": (description or "").strip() + "\n\n#Shorts",
            "tags": tags[:500],
            "categoryId": "22",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    init_resp = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Upload-Content-Length": str(file_size),
            "X-Upload-Content-Type": "video/mp4",
        },
        json=metadata,
        timeout=20,
    )
    if init_resp.status_code != 200:
        return {
            "success": False,
            "error": init_resp.text,
            "status_code": init_resp.status_code,
        }

    upload_url = init_resp.headers.get("Location")
    if not upload_url:
        return {"success": False, "error": "Missing upload URL", "status_code": 500}

    with open(file_path, "rb") as handle:
        upload_resp = requests.put(
            upload_url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "video/mp4",
            },
            data=handle,
            timeout=300,
        )

    if upload_resp.status_code not in (200, 201):
        return {
            "success": False,
            "error": upload_resp.text,
            "status_code": upload_resp.status_code,
        }

    try:
        result = upload_resp.json()
    except Exception:
        result = {}

    video_id = result.get("id")
    return {
        "success": True,
        "video_id": video_id,
        "post_url": f"https://youtube.com/shorts/{video_id}" if video_id else None,
    }


def youtube_upload_from_url(
    account: dict,
    video_url: str,
    title: str,
    description: str,
    tags: Optional[List[str]] = None,
) -> dict:
    tmp_path = download_video_to_temp(video_url)
    try:
        result = youtube_upload_file(account.get("access_token", ""), tmp_path, title, description, tags)
        if not result.get("success") and result.get("status_code") in (401, 403):
            refresh_token = account.get("refresh_token")
            if refresh_token:
                new_token = refresh_google_access_token(refresh_token)
                if new_token:
                    result = youtube_upload_file(new_token, tmp_path, title, description, tags)
                    result["access_token"] = new_token
        return result
    finally:
        tmp_path.unlink(missing_ok=True)


def publish_to_youtube(user_id: str, video_url: str, title: str, description: str, tags: Optional[List[str]] = None) -> dict:
    accounts = (
        supabase.table("social_accounts")
        .select("*")
        .eq("user_id", user_id)
        .eq("provider", "youtube")
        .execute()
    )
    if not accounts.data:
        return {"success": False, "error": "No connected YouTube account"}

    account = accounts.data[0]
    result = youtube_upload_from_url(account, video_url, title, description, tags)
    if result.get("access_token"):
        supabase.table("social_accounts").update(
            {"access_token": result.get("access_token")}
        ).eq("user_id", user_id).eq("provider", "youtube").execute()
    return result


# ==================== TikTok Integration ====================

def tiktok_redirect_uri(request: Request) -> str:
    return os.environ.get("TIKTOK_REDIRECT_URI") or f"{str(request.base_url).rstrip('/')}/api/auth/tiktok/callback"


@app.get("/api/auth/tiktok/start")
def start_tiktok_oauth(request: Request, redirect_url: Optional[str] = None, user_id: str = "demo_user"):
    """Initiate TikTok OAuth flow"""
    client_key = os.environ.get("TIKTOK_CLIENT_KEY")
    if not client_key:
        raise HTTPException(status_code=400, detail="TIKTOK_CLIENT_KEY not configured")

    redirect_uri = tiktok_redirect_uri(request)
    state = encode_oauth_state({
        "redirect": redirect_url,
        "user_id": user_id,
    })

    params = {
        "client_key": client_key,
        "scope": "user.info.basic,video.upload",
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": state,
    }
    auth_url = f"https://www.tiktok.com/v2/auth/authorize/?{urlencode(params)}"
    return {"auth_url": auth_url}


@app.get("/api/auth/tiktok/callback")
def tiktok_oauth_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
):
    """Handle TikTok OAuth callback"""
    payload = decode_oauth_state(state)
    redirect_target = payload.get("redirect") or os.environ.get("FRONTEND_URL") or "http://localhost:3000/dashboard/series/create"

    if error:
        return RedirectResponse(append_query(redirect_target, "error", error))
    if not code:
        return RedirectResponse(append_query(redirect_target, "error", "missing_code"))

    client_key = os.environ.get("TIKTOK_CLIENT_KEY")
    client_secret = os.environ.get("TIKTOK_CLIENT_SECRET")
    if not client_key or not client_secret:
        return RedirectResponse(append_query(redirect_target, "error", "missing_client"))

    # Exchange code for access token
    token_resp = requests.post(
        "https://open.tiktokapis.com/v2/oauth/token/",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_key": client_key,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": tiktok_redirect_uri(request),
        },
        timeout=20,
    )

    if token_resp.status_code != 200:
        return RedirectResponse(append_query(redirect_target, "error", "token_exchange_failed"))

    token_data = token_resp.json()
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")

    if not access_token:
        return RedirectResponse(append_query(redirect_target, "error", "missing_access_token"))

    # Get user profile
    profile_name = "TikTok"
    profile_id = "tiktok"
    try:
        profile_resp = requests.get(
            "https://open.tiktokapis.com/v2/user/info/",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"fields": "open_id,union_id,avatar_url,display_name"},
            timeout=15,
        )
        if profile_resp.status_code == 200:
            user_data = profile_resp.json().get("data", {}).get("user", {})
            profile_id = user_data.get("open_id", profile_id)
            profile_name = user_data.get("display_name", profile_name)
    except Exception as e:
        print(f"TikTok profile fetch failed: {e}")

    # Save to database
    user_id = payload.get("user_id", "demo_user")
    data = {
        "user_id": user_id,
        "provider": "tiktok",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "profile_name": profile_name,
        "profile_id": profile_id,
        "scopes": ["user.info.basic", "video.upload"],
    }
    supabase.table("social_accounts").upsert(data).execute()

    return RedirectResponse(append_query(redirect_target, "connected", "tiktok"))


def refresh_tiktok_access_token(refresh_token: str) -> Optional[str]:
    """Refresh TikTok access token"""
    client_key = os.environ.get("TIKTOK_CLIENT_KEY")
    client_secret = os.environ.get("TIKTOK_CLIENT_SECRET")
    if not client_key or not client_secret:
        return None

    resp = requests.post(
        "https://open.tiktokapis.com/v2/oauth/token/",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_key": client_key,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        timeout=15,
    )

    if resp.status_code != 200:
        return None
    return resp.json().get("access_token")


def tiktok_upload_video(access_token: str, video_url: str, title: str, privacy_level: str = "PUBLIC_TO_EVERYONE") -> dict:
    """
    Upload video to TikTok using Content Posting API
    1. Initialize upload
    2. Upload video bytes
    3. Publish video
    """
    try:
        # Download video
        tmp_path = download_video_to_temp(video_url)

        # Step 1: Initialize upload
        init_resp = requests.post(
            "https://open.tiktokapis.com/v2/post/publish/video/init/",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json; charset=UTF-8",
            },
            json={
                "post_info": {
                    "title": title[:150],
                    "privacy_level": privacy_level,
                    "disable_duet": False,
                    "disable_comment": False,
                    "disable_stitch": False,
                    "video_cover_timestamp_ms": 1000,
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": tmp_path.stat().st_size,
                    "chunk_size": tmp_path.stat().st_size,
                    "total_chunk_count": 1,
                }
            },
            timeout=20,
        )

        if init_resp.status_code != 200:
            tmp_path.unlink(missing_ok=True)
            return {
                "success": False,
                "error": f"Init failed: {init_resp.text}",
                "status_code": init_resp.status_code,
            }

        init_data = init_resp.json()
        publish_id = init_data.get("data", {}).get("publish_id")
        upload_url = init_data.get("data", {}).get("upload_url")

        if not publish_id or not upload_url:
            tmp_path.unlink(missing_ok=True)
            return {"success": False, "error": "Missing publish_id or upload_url"}

        # Step 2: Upload video bytes
        with open(tmp_path, "rb") as video_file:
            upload_resp = requests.put(
                upload_url,
                headers={"Content-Type": "video/mp4"},
                data=video_file,
                timeout=300,
            )

        tmp_path.unlink(missing_ok=True)

        if upload_resp.status_code not in (200, 201):
            return {
                "success": False,
                "error": f"Upload failed: {upload_resp.text}",
                "status_code": upload_resp.status_code,
            }

        # Step 3: Video is automatically published
        return {
            "success": True,
            "publish_id": publish_id,
            "status": "published",
            "post_url": None,  # TikTok doesn't return direct URL immediately
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def publish_to_tiktok(user_id: str, video_url: str, title: str) -> dict:
    """Publish video to TikTok"""
    accounts = (
        supabase.table("social_accounts")
        .select("*")
        .eq("user_id", user_id)
        .eq("provider", "tiktok")
        .execute()
    )
    if not accounts.data:
        return {"success": False, "error": "No connected TikTok account"}

    account = accounts.data[0]
    result = tiktok_upload_video(account.get("access_token", ""), video_url, title)

    # If auth error, try refreshing token
    if not result.get("success") and result.get("status_code") in (401, 403):
        refresh_token = account.get("refresh_token")
        if refresh_token:
            new_token = refresh_tiktok_access_token(refresh_token)
            if new_token:
                result = tiktok_upload_video(new_token, video_url, title)
                if result.get("success"):
                    supabase.table("social_accounts").update(
                        {"access_token": new_token}
                    ).eq("user_id", user_id).eq("provider", "tiktok").execute()

    return result


# ==================== Instagram Integration ====================

def instagram_redirect_uri(request: Request) -> str:
    return os.environ.get("INSTAGRAM_REDIRECT_URI") or f"{str(request.base_url).rstrip('/')}/api/auth/instagram/callback"


@app.get("/api/auth/instagram/start")
def start_instagram_oauth(request: Request, redirect_url: Optional[str] = None, user_id: str = "demo_user"):
    """Initiate Instagram OAuth flow"""
    app_id = os.environ.get("INSTAGRAM_APP_ID")
    if not app_id:
        raise HTTPException(status_code=400, detail="INSTAGRAM_APP_ID not configured")

    redirect_uri = instagram_redirect_uri(request)
    state = encode_oauth_state({
        "redirect": redirect_url,
        "user_id": user_id,
    })

    params = {
        "client_id": app_id,
        "redirect_uri": redirect_uri,
        "scope": "instagram_basic,instagram_content_publish",
        "response_type": "code",
        "state": state,
    }
    auth_url = f"https://api.instagram.com/oauth/authorize?{urlencode(params)}"
    return {"auth_url": auth_url}


@app.get("/api/auth/instagram/callback")
def instagram_oauth_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
):
    """Handle Instagram OAuth callback"""
    payload = decode_oauth_state(state)
    redirect_target = payload.get("redirect") or os.environ.get("FRONTEND_URL") or "http://localhost:3000/dashboard/series/create"

    if error:
        return RedirectResponse(append_query(redirect_target, "error", error))
    if not code:
        return RedirectResponse(append_query(redirect_target, "error", "missing_code"))

    app_id = os.environ.get("INSTAGRAM_APP_ID")
    app_secret = os.environ.get("INSTAGRAM_APP_SECRET")
    if not app_id or not app_secret:
        return RedirectResponse(append_query(redirect_target, "error", "missing_client"))

    # Exchange code for access token
    token_resp = requests.post(
        "https://api.instagram.com/oauth/access_token",
        data={
            "client_id": app_id,
            "client_secret": app_secret,
            "grant_type": "authorization_code",
            "redirect_uri": instagram_redirect_uri(request),
            "code": code,
        },
        timeout=20,
    )

    if token_resp.status_code != 200:
        return RedirectResponse(append_query(redirect_target, "error", "token_exchange_failed"))

    token_data = token_resp.json()
    access_token = token_data.get("access_token")
    user_id_ig = token_data.get("user_id")

    if not access_token:
        return RedirectResponse(append_query(redirect_target, "error", "missing_access_token"))

    # Exchange short-lived token for long-lived token
    long_lived_resp = requests.get(
        "https://graph.instagram.com/access_token",
        params={
            "grant_type": "ig_exchange_token",
            "client_secret": app_secret,
            "access_token": access_token,
        },
        timeout=20,
    )

    if long_lived_resp.status_code == 200:
        long_lived_data = long_lived_resp.json()
        access_token = long_lived_data.get("access_token", access_token)

    # Get Instagram Business Account ID
    profile_name = "Instagram"
    instagram_account_id = None
    try:
        # First, get Facebook Pages
        pages_resp = requests.get(
            f"https://graph.facebook.com/v21.0/{user_id_ig}/accounts",
            params={"access_token": access_token},
            timeout=15,
        )
        if pages_resp.status_code == 200:
            pages = pages_resp.json().get("data", [])
            if pages:
                page_id = pages[0].get("id")
                page_token = pages[0].get("access_token")

                # Get Instagram Business Account from Page
                ig_account_resp = requests.get(
                    f"https://graph.facebook.com/v21.0/{page_id}",
                    params={
                        "fields": "instagram_business_account",
                        "access_token": page_token,
                    },
                    timeout=15,
                )
                if ig_account_resp.status_code == 200:
                    ig_data = ig_account_resp.json()
                    instagram_account_id = ig_data.get("instagram_business_account", {}).get("id")

                    # Get profile name
                    if instagram_account_id:
                        profile_resp = requests.get(
                            f"https://graph.facebook.com/v21.0/{instagram_account_id}",
                            params={
                                "fields": "username",
                                "access_token": page_token,
                            },
                            timeout=15,
                        )
                        if profile_resp.status_code == 200:
                            profile_name = profile_resp.json().get("username", profile_name)
    except Exception as e:
        print(f"Instagram profile fetch failed: {e}")

    # Save to database
    user_id = payload.get("user_id", "demo_user")
    data = {
        "user_id": user_id,
        "provider": "instagram",
        "access_token": access_token,
        "refresh_token": None,  # Instagram uses long-lived tokens
        "profile_name": profile_name,
        "profile_id": instagram_account_id or user_id_ig,
        "scopes": ["instagram_basic", "instagram_content_publish"],
    }
    supabase.table("social_accounts").upsert(data).execute()

    return RedirectResponse(append_query(redirect_target, "connected", "instagram"))


def instagram_upload_reel(access_token: str, instagram_account_id: str, video_url: str, caption: str) -> dict:
    """
    Upload Reel to Instagram
    1. Create media container
    2. Poll for upload completion
    3. Publish media container
    """
    try:
        # Step 1: Create media container
        container_resp = requests.post(
            f"https://graph.facebook.com/v21.0/{instagram_account_id}/media",
            params={
                "media_type": "REELS",
                "video_url": video_url,
                "caption": caption[:2200] if caption else "",
                "share_to_feed": True,
                "access_token": access_token,
            },
            timeout=30,
        )

        if container_resp.status_code != 200:
            return {
                "success": False,
                "error": f"Container creation failed: {container_resp.text}",
                "status_code": container_resp.status_code,
            }

        container_data = container_resp.json()
        creation_id = container_data.get("id")

        if not creation_id:
            return {"success": False, "error": "Missing creation_id"}

        # Step 2: Poll for upload completion (Instagram needs time to process)
        import time
        max_attempts = 30
        for attempt in range(max_attempts):
            status_resp = requests.get(
                f"https://graph.facebook.com/v21.0/{creation_id}",
                params={
                    "fields": "status_code",
                    "access_token": access_token,
                },
                timeout=15,
            )

            if status_resp.status_code == 200:
                status_data = status_resp.json()
                status_code = status_data.get("status_code")

                if status_code == "FINISHED":
                    break
                elif status_code == "ERROR":
                    return {"success": False, "error": "Instagram processing error"}

            if attempt < max_attempts - 1:
                time.sleep(5)  # Wait 5 seconds before next check

        # Step 3: Publish media container
        publish_resp = requests.post(
            f"https://graph.facebook.com/v21.0/{instagram_account_id}/media_publish",
            params={
                "creation_id": creation_id,
                "access_token": access_token,
            },
            timeout=30,
        )

        if publish_resp.status_code not in (200, 201):
            return {
                "success": False,
                "error": f"Publish failed: {publish_resp.text}",
                "status_code": publish_resp.status_code,
            }

        publish_data = publish_resp.json()
        media_id = publish_data.get("id")

        return {
            "success": True,
            "media_id": media_id,
            "post_url": f"https://www.instagram.com/reel/{media_id}" if media_id else None,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def publish_to_instagram(user_id: str, video_url: str, caption: str) -> dict:
    """Publish video to Instagram"""
    accounts = (
        supabase.table("social_accounts")
        .select("*")
        .eq("user_id", user_id)
        .eq("provider", "instagram")
        .execute()
    )
    if not accounts.data:
        return {"success": False, "error": "No connected Instagram account"}

    account = accounts.data[0]
    instagram_account_id = account.get("profile_id")

    if not instagram_account_id:
        return {"success": False, "error": "Instagram Business Account not configured"}

    result = instagram_upload_reel(
        account.get("access_token", ""),
        instagram_account_id,
        video_url,
        caption,
    )

    return result


@app.post("/api/publish/{provider}")
def publish_video(provider: str, video_url: str, caption: Optional[str] = None, user_id: str = "demo_user"):
    provider = provider.lower()
    try:
        if provider == "youtube":
            title = caption or "New Short"
            description = caption or ""
            result = publish_to_youtube(user_id, video_url, title, description, tags=["Shorts"])
            if not result.get("success"):
                raise HTTPException(status_code=500, detail=result.get("error") or "Upload failed")
            return {
                "status": "published",
                "provider": provider,
                "video_url": video_url,
                "video_id": result.get("video_id"),
                "post_url": result.get("post_url"),
            }

        elif provider == "tiktok":
            title = caption or "New Video"
            result = publish_to_tiktok(user_id, video_url, title)
            if not result.get("success"):
                raise HTTPException(status_code=500, detail=result.get("error") or "Upload failed")
            return {
                "status": "published",
                "provider": provider,
                "video_url": video_url,
                "publish_id": result.get("publish_id"),
                "post_url": result.get("post_url"),
            }

        elif provider == "instagram":
            result = publish_to_instagram(user_id, video_url, caption or "")
            if not result.get("success"):
                raise HTTPException(status_code=500, detail=result.get("error") or "Upload failed")
            return {
                "status": "published",
                "provider": provider,
                "video_url": video_url,
                "media_id": result.get("media_id"),
                "post_url": result.get("post_url"),
            }

        else:
            return {
                "status": "queued",
                "provider": provider,
                "video_url": video_url,
                "caption": caption,
                "message": f"Publishing for {provider} not implemented yet",
            }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error publishing video: {e}")
        raise HTTPException(status_code=500, detail="Failed to publish video")


def _run_generate_episode(episode_id: str, topic: str, series: dict):
    try:
        supabase.table("episodes").update({"status": "generating"}).eq("id", episode_id).execute()

        platforms = parse_platforms(series.get("platforms"))

        # Get music tracks - if array is provided, pick one randomly
        music_tracks = series.get("music_tracks", [])
        bgm_track_id = None
        if music_tracks and len(music_tracks) > 0:
            import random
            bgm_track_id = random.choice(music_tracks)
            print(f"[generate_video_task] Selected music track: {bgm_track_id} from {len(music_tracks)} available")

        result = run_async(
            generate_video(
                topic=topic,
                voice=series.get("voice") or "adam",
                art_style=series.get("art_style") or "cinematic",
                niche=series.get("niche") or "entertainment",
                beats_count=beats_for_duration(series.get("video_duration")),
                include_captions=True,
                caption_style=series.get("caption_style") or "karaoke",
                motion_effect=series.get("motion_effect") or "ken_burns",
                bgm_mode="random" if not bgm_track_id else "track",
                bgm_track_id=bgm_track_id,
                assemble=True,
            )
        )

        status = "completed" if result.get("video_url") else "failed"
        supabase.table("episodes").update({
            "status": status,
            "video_url": result.get("video_url", ""),
        }).eq("id", episode_id).execute()

        try:
            supabase.table("videos").insert({
                "user_id": series.get("user_id", "demo_user"),
                "video_id": result.get("video_id"),
                "topic": topic,
                "status": result.get("status"),
                "script": result.get("script"),
                "image_urls": result.get("image_urls"),
                "audio_url": result.get("audio_url"),
                "video_url": result.get("video_url"),
                "config": result.get("config"),
            }).execute()

            if result.get("status") == "assembling":
                job_payload = _build_assembly_payload(
                    result.get("video_id"),
                    result.get("image_urls") or [],
                    result.get("audio_url"),
                    result.get("script") or {},
                    result.get("config") or {},
                    bgm_url=None,
                )
                enqueue_assembly_job(result.get("video_id"), job_payload, source_type="episode", source_id=episode_id)
                _safe_update_video(result.get("video_id"), {
                    "status": "assembling",
                    "assembly_reason": None,
                    "assembly_progress": 1,
                    "assembly_stage": "queued",
                    "assembly_started_at": datetime.now(timezone.utc).isoformat(),
                    "assembly_log": "Queued for assembly",
                })
        except Exception as insert_err:
            print(f"Video insert failed: {insert_err}")

        # Auto-publish to enabled platforms
        if status == "completed":
            script = result.get("script") or {}
            title = (script.get("title") or topic)[:100]
            description = f"{script.get('hook', '')}\n\n{script.get('cta', '')}".strip()
            caption = f"{script.get('hook', '')}\n\n{script.get('cta', '')}".strip()
            user_id = series.get("user_id", "demo_user")
            video_url = result.get("video_url")

            published_to_any = False

            # Publish to YouTube
            if series.get("post_to_youtube"):
                youtube_result = publish_to_youtube(
                    user_id,
                    video_url,
                    title,
                    description,
                    tags=[str(series.get("niche") or "Shorts")],
                )
                if youtube_result.get("success"):
                    published_to_any = True
                    print(f"[generate_video_task] Published to YouTube: {youtube_result.get('post_url')}")
                else:
                    print(f"[generate_video_task] YouTube publish failed: {youtube_result.get('error')}")

            # Publish to TikTok
            if series.get("post_to_tiktok"):
                tiktok_result = publish_to_tiktok(user_id, video_url, title)
                if tiktok_result.get("success"):
                    published_to_any = True
                    print(f"[generate_video_task] Published to TikTok: {tiktok_result.get('publish_id')}")
                else:
                    print(f"[generate_video_task] TikTok publish failed: {tiktok_result.get('error')}")

            # Publish to Instagram
            if series.get("post_to_instagram"):
                instagram_result = publish_to_instagram(user_id, video_url, caption)
                if instagram_result.get("success"):
                    published_to_any = True
                    print(f"[generate_video_task] Published to Instagram: {instagram_result.get('post_url')}")
                else:
                    print(f"[generate_video_task] Instagram publish failed: {instagram_result.get('error')}")

            # Update episode status to published if posted to at least one platform
            if published_to_any:
                supabase.table("episodes").update({
                    "status": "published",
                }).eq("id", episode_id).execute()

    except Exception as e:
        print(f"Error: {e}")
        supabase.table("episodes").update({"status": "failed"}).eq("id", episode_id).execute()


def generate_video_task(episode_id: str, topic: str, series: dict):
    if not supabase:
        return
    if not GENERATION_LOCK.acquire(blocking=False):
        try:
            supabase.table("episodes").update({"status": "queued"}).eq("id", episode_id).execute()
        except Exception as e:
            print(f"[generate_video_task] Failed to keep episode queued: {e}")
        print(f"[generate_video_task] Another job is running. Episode {episode_id} queued.")
        return
    try:
        current_id, current_topic, current_series = episode_id, topic, series
        while current_id:
            _run_generate_episode(current_id, current_topic, current_series)
            gc.collect()
            next_job = _get_next_queued_episode()
            if not next_job:
                break
            current_id, current_topic, current_series = next_job
    finally:
        GENERATION_LOCK.release()


def call_gpt_json(prompt: str, system: str = "", temperature: float = 0.5, fallback: Optional[dict] = None):
    if not client:
        return fallback
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        return json.loads(content) if content else fallback
    except Exception as e:
        print(f"OpenAI error: {e}")
        return fallback


def elevenlabs_list_voices():
    if not ELEVEN_API_KEY:
        raise HTTPException(status_code=400, detail="ELEVENLABS_API_KEY not configured")
    # Serve from cache if fresh
    now = time.time()
    if voice_cache["voices"] and now - voice_cache["ts"] < VOICE_CACHE_TTL:
        return voice_cache["voices"]
    try:
        resp = requests.get(
            "https://api.elevenlabs.io/v1/voices",
            headers={"xi-api-key": ELEVEN_API_KEY},
            timeout=10,
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="Failed to fetch voices")
        data = resp.json()
        voices = data.get("voices", [])
        voice_cache["voices"] = voices
        voice_cache["ts"] = now
        return voices
    except HTTPException:
        raise
    except Exception as e:
        print(f"ElevenLabs voices error: {e}")
        raise HTTPException(status_code=500, detail="Unable to fetch voices")


def elevenlabs_synthesize(text: str, voice_id: Optional[str] = None):
    if not ELEVEN_API_KEY:
        raise HTTPException(status_code=400, detail="ELEVENLABS_API_KEY not configured")
    voice = voice_id or DEFAULT_ELEVEN_VOICE
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.4, "similarity_boost": 0.7},
    }
    try:
        resp = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice}",
            headers={
                "xi-api-key": ELEVEN_API_KEY,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=20,
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="TTS request failed")
        audio_bytes = resp.content
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        return {"voice_id": voice, "audio_base64": audio_b64, "content_type": "audio/mpeg"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"ElevenLabs synth error: {e}")
        raise HTTPException(status_code=500, detail="Unable to synthesize audio")


@app.post("/api/analyze-viral-score")
def analyze_viral_score(request: ViralScoreRequest, _: bool = Depends(rate_limiter)):
    base_script = request.script.strip()
    if not base_script:
        raise HTTPException(status_code=400, detail="Script is required")

    system = "You are a short-form video expert. Score and improve scripts."
    user_prompt = f"""
    Analyze the following script or topic for viral potential. Return JSON with:
    - score (0-100)
    - breakdown (hook, emotion, curiosity, trending - each 0-25)
    - strengths (array of strings)
    - improvements (array of strings)
    - optimized_script (improved version)
    
    Script/Topic: {base_script}
    """
    fallback = {
        "score": 75,
        "breakdown": {"hook": 18, "emotion": 20, "curiosity": 20, "trending": 17},
        "strengths": ["Clear hook", "Good pacing"],
        "improvements": ["Increase emotional language", "Add explicit CTA"],
        "optimized_script": base_script,
    }
    result = call_gpt_json(
        user_prompt,
        system=system,
        fallback=fallback,
        temperature=0.6,
    )
    if not result:
        raise HTTPException(status_code=500, detail="Unable to generate viral score")
    return result


def get_ai_trends(niche: str) -> dict:
    """Use GPT to generate trending topics when pytrends fails"""
    if not client:
        return None
    
    prompt = f"""
    Generate 6 currently trending topics in the "{niche}" niche for short-form video content (TikTok, Instagram Reels, YouTube Shorts).
    
    Return JSON with this exact structure:
    {{
        "trending_topics": [
            {{"topic": "Topic Name", "growth": "+XXX%", "search_volume": 12000, "reason": "Why it's trending"}},
            ...
        ],
        "suggested_titles": [
            "Viral video title idea 1",
            "Viral video title idea 2",
            "Viral video title idea 3"
        ],
        "trending_music": [
            {{"name": "Song/Sound Name", "uses": "1.2M"}},
            {{"name": "Another Sound", "uses": "890K"}}
        ]
    }}
    
    Make the topics realistic, timely, and based on what would actually trend in {niche} content in late 2024/2025.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.7,
            messages=[
                {"role": "system", "content": "You are a social media trend analyst specializing in viral short-form video content."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        return json.loads(content) if content else None
    except Exception as e:
        print(f"AI trends error: {e}")
        return None


# Niche-specific search terms that work better with Google Trends
NICHE_SEARCH_TERMS = {
    "horror": ["horror movies", "scary stories", "creepypasta", "haunted places", "true crime horror"],
    "paranormal": ["ghosts", "UFO sightings", "paranormal activity", "haunted houses", "supernatural"],
    "sci-fi": ["AI technology", "space exploration", "futuristic", "robots", "sci-fi movies"],
    "motivation": ["self improvement", "productivity", "success mindset", "morning routine", "hustle culture"],
    "finance": ["stock market", "cryptocurrency", "investing tips", "passive income", "real estate investing"],
    "tech": ["artificial intelligence", "new iPhone", "gaming PC", "tech gadgets", "software development"],
    "history": ["ancient history", "world war", "historical mysteries", "ancient civilizations", "medieval"],
    "mystery": ["unsolved mysteries", "conspiracy theories", "true crime", "cold cases", "unexplained"],
}


@app.get("/api/trends/{niche}")
def get_trends(niche: str, _: bool = Depends(rate_limiter)):
    """
    Fetch rising topics using Google Trends with better search terms.
    Falls back to AI-generated trends if Google returns empty data.
    Tries platform-level trends via RapidAPI TikTok if a key is provided.
    """
    
    # TikTok RapidAPI integration (optional)
    rapidapi_key = os.environ.get("RAPIDAPI_TIKTOK_KEY")
    rapidapi_host = os.environ.get("RAPIDAPI_TIKTOK_HOST", "tiktok-all-in-one.p.rapidapi.com")

    if rapidapi_key:
        try:
            import httpx
            url = f"https://{rapidapi_host}/trending/feed"
            headers = {
                "x-rapidapi-key": rapidapi_key,
                "x-rapidapi-host": rapidapi_host,
            }
            params = {"region": "US", "count": 10}
            resp = httpx.get(url, headers=headers, params=params, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                videos = data.get("aweme_list") or data.get("data") or []
                topics = []
                for idx, item in enumerate(videos[:6]):
                    desc = item.get("desc") or f"Trending #{idx+1}"
                    stats = item.get("statistics", {})
                    history = [{"label": f"{i+1}", "value": max(5, (stats.get("play_count", 0) // 1000) % 120 + i * 2)} for i in range(12)]
                    topics.append({
                        "topic": desc[:80],
                        "growth": "+100%",
                        "search_volume": stats.get("play_count", 0),
                        "reason": "TikTok trending feed",
                        "history": history,
                    })
                if topics:
                    return {
                        "trending_topics": topics,
                        "suggested_titles": [t["topic"] for t in topics[:3]],
                        "trending_music": [],
                        "source": "tiktok_trending",
                    }
            else:
                print(f"TikTok RapidAPI error: {resp.status_code} {resp.text}")
        except Exception as rapid_err:
            print(f"TikTok RapidAPI exception: {rapid_err}")

    # Get better search terms for this niche
    search_terms = NICHE_SEARCH_TERMS.get(niche.lower(), [niche])
    
    # Try pytrends with proxy
    try:
        from pytrends.request import TrendReq
        import random
        
        proxy_url = os.environ.get("GOOGLE_TRENDS_PROXY")
        proxies = []
        
        if proxy_url:
            # Rotate proxy number for different IP
            proxy_num = random.randint(1, 200)
            rotated_proxy = proxy_url.replace("qdmchnug-1", f"qdmchnug-{proxy_num}")
            if "qdmchnug-" not in proxy_url:
                rotated_proxy = proxy_url
            rotated_proxy = rotated_proxy.rstrip("/")  # avoid trailing slash breaking auth
            proxies = [rotated_proxy]
        
        print(f"Trying pytrends with proxies: {proxies}")

        # Helper to create varied synthetic histories
        def synthetic_history(seed: int = 1):
            base = 70 + (seed % 10) * 2
            return [
                {
                    "label": f"{i+1}",
                    "value": max(
                        3,
                        base
                        - i * (3 + (seed % 4))
                        + (i % 3) * 5
                        + ((seed + i * 7) % 12),
                    ),
                }
                for i in range(12)
            ]

        def attach_history(topics: list[dict]):
            for idx, t in enumerate(topics):
                if "history" not in t or not t.get("history"):
                    t["history"] = synthetic_history((abs(hash(t.get("topic", ""))) + idx) % 97)
            return topics
        
        # Initialize pytrends
        pytrends = None
        if proxies:
            try:
                pytrends = TrendReq(
                    hl='en-US', 
                    tz=360, 
                    timeout=(10, 25),
                    proxies={"https": proxies[0], "http": proxies[0]},
                    retries=2,
                    backoff_factor=0.5
                )
                print("Pytrends init with proxy succeeded")
            except Exception as proxy_err:
                print(f"Pytrends init with proxy failed: {proxy_err}")
        if pytrends is None:
            try:
                pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))
                print("Pytrends init without proxy")
            except Exception as direct_err:
                print(f"Pytrends direct init failed: {direct_err}")
                raise direct_err
        
        all_topics = []
        
        def build_history(keyword: str):
            """Return interest over time series or synthetic curve."""
            try:
                pytrends.build_payload([keyword], timeframe="now 7-d", geo="US")
                hist_df = pytrends.interest_over_time()
                if hist_df is not None and not hist_df.empty and keyword in hist_df:
                    series = hist_df[keyword].tail(12)
                    history = []
                    for idx, val in enumerate(series):
                        history.append({"label": f"{idx+1}", "value": int(val) if val is not None else 0})
                    if history:
                        return history
            except Exception as hist_err:
                print(f"History fetch failed for {keyword}: {hist_err}")
            return synthetic_history(abs(hash(keyword)) % 17)
        
        def trending_searches_fallback():
            try:
                trending_df = pytrends.trending_searches(pn="united_states")
                topics = []
                for idx, row in trending_df.head(6).iterrows():
                    title = str(row.iloc[0]) if len(row) > 0 else f"Trend {idx+1}"
                    topics.append({
                        "topic": title,
                        "growth": "+100%",
                        "search_volume": 100,
                        "reason": "Google trending searches",
                        "history": build_history(title),
                    })
                if topics:
                    return {
                        "trending_topics": topics,
                        "suggested_titles": [
                            f"The Truth About {topics[0]['topic']}",
                            f"Why {topics[0]['topic']} Is Blowing Up",
                            f"{topics[0]['topic']} in 60 Seconds",
                        ],
                        "trending_music": [
                            {"name": "Trending Synthwave", "uses": "2.1M"},
                            {"name": "Viral Strings", "uses": "1.6M"},
                        ],
                        "source": "google_trends_trending",
                    }
            except Exception as e:
                print(f"Trending searches fallback error: {e}")
            return None
        
        # Try each search term until we get results
        for search_term in search_terms[:3]:  # Try up to 3 terms
            try:
                print(f"Trying search term: {search_term}")
                pytrends.build_payload([search_term], cat=0, timeframe="now 7-d", geo="US", gprop="")
                
                # Try related_queries first (more reliable)
                related_queries = pytrends.related_queries()
                if related_queries and search_term in related_queries:
                    rising = related_queries[search_term].get("rising")
                    if rising is not None and not rising.empty and len(rising) > 0:
                        for _, row in rising.head(4).iterrows():
                            query = row.get("query")
                            value = row.get("value", 0)
                            if query and str(query).strip():
                                history = build_history(str(query))
                                all_topics.append({
                                    "topic": str(query).title(),
                                    "growth": f"+{value}%" if value else "+100%",
                                    "search_volume": int(value) * 50 if value else 5000,
                                    "reason": f"Rising search in {search_term}",
                                    "history": history,
                                })
                        print(f"Found {len(all_topics)} topics from related_queries")
                
                # Also try related_topics
                if len(all_topics) < 6:
                    related_topics = pytrends.related_topics()
                    if related_topics and search_term in related_topics:
                        rising = related_topics[search_term].get("rising")
                        if rising is not None and not rising.empty and len(rising) > 0:
                            for _, row in rising.head(4).iterrows():
                                topic_title = row.get("topic_title")
                                value = row.get("value", 0)
                                if topic_title and str(topic_title).strip():
                                    # Avoid duplicates
                                    if not any(t["topic"].lower() == str(topic_title).lower() for t in all_topics):
                                        history = build_history(str(topic_title))
                                        all_topics.append({
                                            "topic": str(topic_title),
                                            "growth": f"+{value}%" if value else "+100%",
                                            "search_volume": int(value) * 100 if value else 10000,
                                            "reason": f"Trending topic in {search_term}",
                                            "history": history,
                                        })
                            print(f"Now have {len(all_topics)} topics after related_topics")
                
                if len(all_topics) >= 4:
                    break  # We have enough
                    
            except Exception as term_error:
                print(f"Error with search term '{search_term}': {term_error}")
                continue
        
        # If we got results from Google Trends
        if all_topics:
            # Deduplicate and limit to 6
            seen = set()
            unique_topics = []
            for t in all_topics:
                topic_lower = t["topic"].lower()
                if topic_lower not in seen:
                    seen.add(topic_lower)
                    unique_topics.append(t)
            
            unique_topics = unique_topics[:6]
            
            return {
                "trending_topics": unique_topics,
                "suggested_titles": [
                    f"The Truth About {unique_topics[0]['topic']} Nobody Tells You",
                    f"Why {unique_topics[0]['topic']} Is Taking Over",
                    f"{unique_topics[0]['topic']} Explained in 60 Seconds",
                ] if unique_topics else [],
                "trending_music": [
                    {"name": "Suspense Orchestra", "uses": "2.3M"},
                    {"name": "Dramatic Reveal", "uses": "1.8M"},
                ],
                "source": "google_trends"
            }
        
        trending_result = trending_searches_fallback()
        if trending_result:
            return trending_result
                    
    except Exception as e:
        print(f"Pytrends error: {e}")
    
    # Fallback to AI-generated trends
    print("Falling back to AI trends...")
    ai_trends = get_ai_trends(niche)
    if ai_trends:
        ai_trends["source"] = "ai_generated"
        ai_trends["trending_topics"] = attach_history(ai_trends.get("trending_topics", []))
        return ai_trends
    
    # Ultimate fallback with varied synthetic histories
    fallback_topics = [
        {"topic": f"{niche.title()} Secrets Revealed", "growth": "+180%", "search_volume": 25000, "reason": "Curiosity-driven content"},
        {"topic": f"Dark Side of {niche.title()}", "growth": "+150%", "search_volume": 18000, "reason": "Controversy drives engagement"},
        {"topic": f"{niche.title()} Facts Nobody Knows", "growth": "+120%", "search_volume": 15000, "reason": "Educational content trending"},
        {"topic": f"Why {niche.title()} Changed Everything", "growth": "+95%", "search_volume": 12000, "reason": "Transformation stories"},
    ]
    fallback_topics = attach_history(fallback_topics)

    return {
        "trending_topics": fallback_topics,
        "suggested_titles": [
            f"The {niche.title()} Hack That Changed My Life",
            f"Why Nobody Talks About This {niche.title()} Secret",
        ],
        "trending_music": [
            {"name": "Suspense Orchestra", "uses": "2.3M"},
            {"name": "Dramatic Reveal", "uses": "1.8M"},
        ],
        "source": "default"
    }


@app.post("/api/generate-series-plan")
def generate_series_plan(request: SeriesPlanRequest, _: bool = Depends(rate_limiter)):
    if request.num_episodes < 3 or request.num_episodes > 30:
        raise HTTPException(status_code=400, detail="num_episodes must be between 3 and 30")

    base_prompt = f"""
    Create a connected {request.num_episodes}-episode short-form video series.
    Topic: {request.topic}
    Niche: {request.niche or "general"}
    
    Return JSON with:
    - series_name: catchy series name
    - description: brief description
    - episodes: array of objects with episode_number, title, hook, description, cliffhanger
    - posting_schedule: array of day names
    """
    fallback = {
        "series_name": f"{request.topic.title()} Deep Dive",
        "description": f"A {request.num_episodes}-part series about {request.topic}.",
        "episodes": [
            {
                "episode_number": i + 1,
                "title": f"Episode {i+1}",
                "hook": "Engaging hook",
                "description": "Episode outline",
                "cliffhanger": "Stay tuned",
            }
            for i in range(request.num_episodes)
        ],
        "posting_schedule": ["Monday", "Wednesday", "Friday", "Sunday", "Tuesday", "Thursday", "Saturday"][:request.num_episodes],
    }
    result = call_gpt_json(
        base_prompt,
        system="You design serialized short-form content with cliffhangers.",
        fallback=fallback,
        temperature=0.7,
    )
    if not result:
        raise HTTPException(status_code=500, detail="Unable to generate series plan")
    return result


@app.post("/api/episodes/{episode_id}/stats")
def update_episode_stats(episode_id: str, stats: EpisodeStats, _: bool = Depends(rate_limiter)):
    try:
        update_data = {k: v for k, v in stats.dict().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No stats provided")
        result = supabase.table("episodes").update(update_data).eq("id", episode_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Episode not found")

        snapshot_fields = {key: update_data.get(key) for key in ["views", "likes", "shares"] if update_data.get(key) is not None}
        if snapshot_fields.get("views") is not None:
            try:
                supabase.table("analytics_snapshots").insert({
                    "episode_id": episode_id,
                    "views": snapshot_fields.get("views", 0),
                    "likes": snapshot_fields.get("likes", 0) or 0,
                    "shares": snapshot_fields.get("shares", 0) or 0,
                }).execute()
            except Exception as e:
                print(f"Snapshot insert failed: {e}")

        return {"status": "updated", "episode": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Episode stats error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update stats")


@app.get("/api/analytics/{user_id}")
def analytics_dashboard(user_id: str, _: bool = Depends(rate_limiter)):
    try:
        episodes_response = supabase.table("episodes").select("*").execute()
        episodes = episodes_response.data or []

        total_views = sum(e.get("views", 0) or 0 for e in episodes)
        total_videos = len(episodes)
        total_likes = sum(e.get("likes", 0) or 0 for e in episodes)
        avg_views = int(total_views / total_videos) if total_videos else 0
        engagement_rate = f"{round((total_likes / total_views) * 100, 1)}%" if total_views else "0%"

        best = None
        for e in episodes:
            if best is None or (e.get("views", 0) or 0) > (best.get("views", 0) or 0):
                best = e

        niche_map: dict[str, list[int]] = defaultdict(list)
        for e in episodes:
            niche = e.get("niche") or e.get("category") or "general"
            niche_map[niche].append(e.get("views", 0) or 0)
        performance_by_niche = [
            {"niche": k, "avg_views": int(sum(v) / len(v)) if v else 0, "count": len(v)}
            for k, v in niche_map.items()
        ]

        day_map: dict[str, list[int]] = defaultdict(list)
        for e in episodes:
            posted_at = e.get("posted_at") or e.get("created_at")
            if not posted_at:
                continue
            try:
                day = time.strftime("%A", time.strptime(posted_at.split("T")[0], "%Y-%m-%d"))
                day_map[day].append(e.get("views", 0) or 0)
            except Exception:
                continue
        performance_by_day = [
            {"day": k, "avg_views": int(sum(v) / len(v)) if v else 0} for k, v in day_map.items()
        ]

        recommendations = []
        if performance_by_niche:
            best_niche = max(performance_by_niche, key=lambda x: x["avg_views"])
            recommendations.append(f"Your {best_niche['niche']} videos perform best.")
        if performance_by_day:
            best_day = max(performance_by_day, key=lambda x: x["avg_views"])
            recommendations.append(f"Posting on {best_day['day']} yields higher views.")
        if avg_views:
            recommendations.append("Maintain videos under 45 seconds for stronger completion.")

        return {
            "total_views": total_views,
            "total_videos": total_videos,
            "avg_views_per_video": avg_views,
            "total_likes": total_likes,
            "engagement_rate": engagement_rate,
            "best_performing": best or {},
            "performance_by_niche": performance_by_niche,
            "performance_by_day": performance_by_day,
            "recommendations": recommendations,
        }
    except Exception as e:
        print(f"Analytics error: {e}")
        raise HTTPException(status_code=500, detail="Failed to load analytics")


@app.post("/api/clone-video")
def clone_video(payload: CloneRequest, _: bool = Depends(rate_limiter)):
    transcript_text = payload.transcript

    if payload.video_url and not transcript_text:
        try:
            from yt_dlp import YoutubeDL
            
            with tempfile.TemporaryDirectory() as tmpdir:
                ydl_opts = {
                    "outtmpl": f"{tmpdir}/%(id)s.%(ext)s",
                    "format": "bestaudio/best",
                    "quiet": True,
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }],
                }
                
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(payload.video_url, download=True)
                    video_id = info.get("id", "video")
                    filepath = f"{tmpdir}/{video_id}.mp3"
                    
                    if client and os.path.exists(filepath):
                        with open(filepath, "rb") as audio_file:
                            transcript_response = client.audio.transcriptions.create(
                                model="whisper-1",
                                file=audio_file
                            )
                            transcript_text = transcript_response.text
        except Exception as e:
            print(f"Clone transcribe error: {e}")
            transcript_text = transcript_text or "Sample transcript content for analysis."

    if not transcript_text:
        raise HTTPException(status_code=400, detail="Provide a video_url or transcript")

    prompt = f"""
    Analyze the following transcript and extract a reusable template.
    
    Return JSON with:
    - analysis: object with hook_type, pacing, structure (array), tone, music_mood, avg_scene_duration
    - extracted_template: string describing the format
    - suggested_topics: array of 3 topic suggestions
    
    Transcript: {transcript_text[:4000]}
    """
    fallback = {
        "analysis": {
            "hook_type": "question",
            "pacing": "fast",
            "structure": ["hook", "problem", "buildup", "reveal", "cta"],
            "tone": "informative",
            "music_mood": "energetic",
            "avg_scene_duration": 3.5,
        },
        "extracted_template": "Opens with a bold question, stacks 3 proof points, reveals a twist, and ends with CTA.",
        "suggested_topics": [
            "Apply this format to: Bermuda Triangle mysteries",
            "Apply this format to: Ancient Egypt secrets",
            "Apply this format to: Deep ocean discoveries",
        ],
    }
    result = call_gpt_json(
        prompt,
        system="You are a viral video reverse engineer. Respond in JSON.",
        fallback=fallback,
        temperature=0.65,
    )
    if not result:
        raise HTTPException(status_code=500, detail="Unable to analyze video")
    return result


@app.post("/api/apply-template")
def apply_template(payload: ApplyTemplateRequest, _: bool = Depends(rate_limiter)):
    if not payload.analysis or not payload.topic:
        raise HTTPException(status_code=400, detail="analysis and topic are required")

    prompt = f"""
    Using the following analysis, write a new script for topic "{payload.topic}".
    
    Analysis: {json.dumps(payload.analysis)}
    
    Return JSON with:
    - script: the full script text
    - cta: call to action text
    """
    fallback = {
        "script": f"Hooking intro about {payload.topic}. Present 3 key points, reveal a twist, and end with a call to action.",
        "cta": "Follow for part 2!",
    }
    result = call_gpt_json(
        prompt,
        system="You recreate scripts using provided templates. Respond with JSON including script and cta.",
        fallback=fallback,
        temperature=0.7,
    )
    if not result:
        raise HTTPException(status_code=500, detail="Unable to apply template")
    return result


@app.get("/api/voices")
def list_voices(_: Request):
    """
    List available ElevenLabs voices. Requires ELEVENLABS_API_KEY.
    """
    voices = elevenlabs_list_voices()
    limited = voices[:VOICE_MAX_RETURN] if voices else []
    return {"voices": limited}


@app.post("/api/voices/preview")
def synth_voice_preview(payload: VoicePreviewRequest, request: Request, _: bool = Depends(voice_rate_limiter)):
    """
    Generate a short audio preview for a given text and voice.
    Enforces a short max length to control costs.
    """
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    if len(text) > 320:
        raise HTTPException(status_code=400, detail="Preview text too long; limit to 320 characters")

    result = elevenlabs_synthesize(text, payload.voice_id)
    return result


@app.post("/api/generate-video")
async def api_generate_video(payload: VideoGenerateRequest, http_request: Request, _: bool = Depends(rate_limiter)):
    """
    AI Director: One-click video generation
    """
    try:
        if not client:
            raise HTTPException(status_code=503, detail="OpenAI API not configured")
        
        callback_url = os.environ.get("ASSEMBLY_CALLBACK_URL")
        if not callback_url:
            base_url = str(http_request.base_url).rstrip("/")
            callback_url = f"{base_url}/api/assembly/callback"
        callback_token = os.environ.get("ASSEMBLY_CALLBACK_TOKEN")

        result = await generate_video(
            topic=payload.topic,
            voice=payload.voice,
            art_style=payload.art_style,
            niche=payload.niche,
            beats_count=payload.beats_count,
            include_captions=payload.include_captions,
            caption_style=payload.caption_style,
            motion_effect=payload.motion_effect,
            bgm_mode=payload.bgm_mode,
            bgm_track_id=payload.bgm_track_id,
            bgm_custom_url=payload.bgm_custom_url,
            assemble=payload.assemble,
            callback_url=callback_url,
            callback_token=callback_token,
        )

        # Store result if Supabase is available
        if supabase:
            try:
                supabase.table("director_videos").insert({
                    "user_id": "demo_user",
                    "video_id": result["video_id"],
                    "topic": payload.topic,
                    "status": result["status"],
                    "script": result["script"],
                    "image_urls": result["image_urls"],
                    "audio_url": result.get("audio_url"),
                    "video_url": result.get("video_url"),
                    "config": result["config"],
                }).execute()

                if result.get("status") == "assembling":
                    bgm_url = payload.bgm_custom_url if payload.bgm_mode == "custom" else None
                    job_payload = _build_assembly_payload(
                        result["video_id"],
                        result.get("image_urls") or [],
                        result.get("audio_url"),
                        result.get("script") or {},
                        result.get("config") or {},
                        bgm_url=bgm_url,
                    )
                    enqueue_assembly_job(result["video_id"], job_payload, source_type="director")
                    supabase.table("director_videos").update({
                        "status": "assembling",
                        "assembly_progress": 1,
                        "assembly_stage": "queued",
                        "assembly_started_at": datetime.now(timezone.utc).isoformat(),
                        "assembly_log": "Queued for assembly",
                    }).eq("video_id", result["video_id"]).execute()
            except Exception as e:
                print(f"[WARNING] Failed to store video metadata: {e}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"Video generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/assembly/callback")
async def assembly_callback(payload: AssemblyCallbackRequest, request: Request):
    """Receive assembly progress updates from Modal workers."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")

    token = os.environ.get("ASSEMBLY_CALLBACK_TOKEN")
    if token:
        auth = request.headers.get("Authorization")
        if auth != f"Bearer {token}":
            raise HTTPException(status_code=401, detail="Unauthorized")

    fields: dict = {}
    if payload.status:
        fields["status"] = payload.status
    if payload.progress is not None:
        fields["assembly_progress"] = int(payload.progress)
    if payload.stage:
        fields["assembly_stage"] = payload.stage
    if payload.eta_seconds is not None:
        fields["assembly_eta_seconds"] = int(payload.eta_seconds)
    if payload.elapsed_seconds is not None:
        fields["assembly_elapsed_seconds"] = int(payload.elapsed_seconds)
    if payload.started_at:
        fields["assembly_started_at"] = payload.started_at
    if payload.completed_at:
        fields["assembly_completed_at"] = payload.completed_at
    if payload.log:
        fields["assembly_log"] = payload.log
    if payload.reason:
        fields["assembly_reason"] = payload.reason
    if payload.video_url:
        fields["video_url"] = payload.video_url
        if not payload.status:
            fields["status"] = "completed"

    current_status = None
    try:
        # Check director_videos first, then fallback to old videos table
        current = supabase.table("director_videos").select("status").eq("video_id", payload.video_id).execute()
        if not current.data:
            current = supabase.table("videos").select("status").eq("video_id", payload.video_id).execute()
        if current.data:
            current_status = current.data[0].get("status")
    except Exception as e:
        print(f"Assembly callback status check error: {e}")

    if current_status == "assembly_canceled":
        for key in (
            "status",
            "assembly_progress",
            "assembly_stage",
            "assembly_eta_seconds",
            "assembly_elapsed_seconds",
            "assembly_reason",
        ):
            fields.pop(key, None)

    if payload.status == "completed" and current_status != "assembly_canceled":
        fields.setdefault("assembly_progress", 100)
        fields.setdefault("assembly_eta_seconds", 0)
        fields.setdefault("assembly_completed_at", datetime.now(timezone.utc).isoformat())

    if not fields:
        return {"status": "no_update"}

    try:
        update = _safe_update_video(payload.video_id, fields)
        if update and update.data:
            return update.data[0]
        return {"status": "ok"}
    except Exception as e:
        print(f"Assembly callback error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update assembly status")


@app.get("/api/video/{video_id}")
async def get_video_status(video_id: str):
    """Get video generation status"""
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")

    try:
        # Check director_videos first (new schema)
        result = supabase.table("director_videos").select("*").eq("video_id", video_id).execute()
        if result.data:
            return _maybe_reconcile_video(result.data[0])

        # Fallback to old videos table for backward compatibility
        result = supabase.table("videos").select("*").eq("video_id", video_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Video not found")
        record = result.data[0]

        return _maybe_reconcile_video(record)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch video status")


@app.post("/api/video/{video_id}/assemble")
async def retry_assemble(video_id: str, background_tasks: BackgroundTasks, request: Request):
    """Retry assembling a video using existing assets (fire-and-forget)"""
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")

    try:
        # Check director_videos first, then fallback to old videos table
        result = supabase.table("director_videos").select("*").eq("video_id", video_id).execute()
        if not result.data:
            result = supabase.table("videos").select("*").eq("video_id", video_id).execute()
            if not result.data:
                raise HTTPException(status_code=404, detail="Video not found")
        record = result.data[0]

        if (record.get("status") or "").lower() == "assembling":
            started_at = _parse_timestamp(record.get("assembly_started_at") or record.get("updated_at"))
            if started_at:
                elapsed = datetime.now(timezone.utc) - started_at
                if elapsed.total_seconds() < ASSEMBLY_RETRY_COOLDOWN_SECONDS:
                    return record
            else:
                return record

        modal_url = os.environ.get("MODAL_ASSEMBLE_URL") or os.environ.get("MODAL_WEBHOOK_URL")
        assembly_backend = _resolve_assembly_backend(modal_url)
        use_queue = assembly_backend == "queue"
        use_local = assembly_backend == "local"
        if assembly_backend == "modal" and not modal_url:
            raise HTTPException(status_code=500, detail="Modal URL not configured")

        # Update status to indicate assembly is starting
        log_label = (
            "Queued for assembly (queue)"
            if use_queue
            else "Queued for assembly (local)" if use_local else "Queued for assembly (modal)"
        )
        _safe_update_video(video_id, {
            "status": "assembling",
            "assembly_reason": None,
            "assembly_progress": 1,
            "assembly_stage": "queued",
            "assembly_started_at": datetime.now(timezone.utc).isoformat(),
            "assembly_elapsed_seconds": 0,
            "assembly_eta_seconds": None,
            "assembly_log": log_label,
        })

        callback_url = os.environ.get("ASSEMBLY_CALLBACK_URL")
        if not callback_url:
            base_url = str(request.base_url).rstrip("/")
            callback_url = f"{base_url}/api/assembly/callback"
        callback_token = os.environ.get("ASSEMBLY_CALLBACK_TOKEN")

        if use_queue:
            job_payload = _build_assembly_payload(
                video_id,
                record.get("image_urls", []),
                record.get("audio_url"),
                record.get("script", {}) or {},
                record.get("config", {}) or {},
            )
            # Check if this is a director video or episode
            source_type = "director"
            source_id_val = None
            try:
                director_check = supabase.table("director_videos").select("id").eq("video_id", video_id).execute()
                if director_check.data:
                    source_id_val = director_check.data[0].get("id")
                else:
                    episode_check = supabase.table("episodes").select("id").eq("video_id", video_id).execute()
                    if episode_check.data:
                        source_type = "episode"
                        source_id_val = episode_check.data[0].get("id")
            except Exception as e:
                print(f"[reassemble] Warning: Could not determine source type: {e}")

            enqueue_assembly_job(video_id, job_payload, source_type=source_type, source_id=source_id_val)
        elif use_local:
            start_time = time.monotonic()
            last_cancel_check = 0.0

            def should_cancel() -> bool:
                nonlocal last_cancel_check
                if not supabase:
                    return False
                now = time.monotonic()
                if now - last_cancel_check < 5:
                    return False
                last_cancel_check = now
                try:
                    # Check director_videos first, then fallback to old videos table
                    current = supabase.table("director_videos").select("status").eq("video_id", video_id).execute()
                    if not current.data:
                        current = supabase.table("videos").select("status").eq("video_id", video_id).execute()
                    if current.data and current.data[0].get("status") == "assembly_canceled":
                        return True
                except Exception as status_err:
                    print(f"[assembly] Status check failed: {status_err}")
                return False

            def report_progress(payload: dict) -> None:
                if should_cancel():
                    return
                progress = payload.get("progress")
                stage = payload.get("stage")
                log_line = payload.get("log")
                elapsed = int(time.monotonic() - start_time)
                eta_seconds = None
                if isinstance(progress, int) and progress > 0:
                    eta_seconds = max(0, int(elapsed * (100 - progress) / progress))
                update_fields = {
                    "status": "assembling",
                    "assembly_progress": progress,
                    "assembly_stage": stage,
                    "assembly_log": log_line,
                    "assembly_elapsed_seconds": elapsed,
                    "assembly_eta_seconds": eta_seconds,
                }
                _safe_update_video(video_id, {k: v for k, v in update_fields.items() if v is not None})

            async def trigger_local():
                try:
                    video_url, local_error = await asyncio.to_thread(
                        assemble_video_local_sync,
                        video_id,
                        record.get("image_urls", []),
                        record.get("audio_url"),
                        record.get("script", {}).get("beats", []),
                        720,
                        1280,
                        30,
                        report_progress,
                        should_cancel,
                    )
                    if should_cancel():
                        return
                    if video_url:
                        _safe_update_video(video_id, {
                            "status": "completed",
                            "video_url": video_url,
                            "assembly_progress": 100,
                            "assembly_stage": "completed",
                            "assembly_eta_seconds": 0,
                            "assembly_completed_at": datetime.now(timezone.utc).isoformat(),
                            "assembly_log": "Assembly completed",
                        })
                    else:
                        if local_error == "Canceled by user":
                            return
                        _safe_update_video(video_id, {
                            "status": "assembly_failed",
                            "assembly_reason": local_error or "Local assembly failed",
                            "assembly_stage": "failed",
                            "assembly_log": "Local assembly failed",
                        })
                except Exception as e:
                    print(f"Local assembly error for {video_id}: {e}")
                    if should_cancel():
                        return
                    _safe_update_video(video_id, {
                        "status": "assembly_failed",
                        "assembly_reason": f"Local assembly error: {str(e)}",
                        "assembly_stage": "failed",
                        "assembly_log": "Local assembly failed",
                    })

            background_tasks.add_task(trigger_local)
        else:
            # Trigger Modal assembly in background (fire-and-forget)
            payload = {
                "video_id": video_id,
                "image_urls": record.get("image_urls", []),
                "audio_url": record.get("audio_url"),
                "durations": [b.get("duration", 4) for b in record.get("script", {}).get("beats", [])],
                "beats": record.get("script", {}).get("beats", []),
                "include_captions": record.get("config", {}).get("include_captions", True),
                "caption_style": record.get("config", {}).get("caption_style", "karaoke"),
                "motion_effect": record.get("config", {}).get("motion_effect", "ken_burns"),
                "output_width": 1080,
                "output_height": 1920,
                "fps": 30,
                "callback_url": callback_url,
                "callback_token": callback_token,
            }

            # Fire-and-forget: trigger Modal and return immediately
            async def trigger_modal():
                try:
                    async with httpx.AsyncClient(timeout=3000.0) as client:
                        await client.post(modal_url, json=payload)
                except Exception as e:
                    print(f"Modal trigger error for {video_id}: {e}")
                    _safe_update_video(video_id, {
                        "status": "assembly_failed",
                        "assembly_reason": f"Failed to trigger assembly: {str(e)}",
                        "assembly_stage": "trigger_failed",
                        "assembly_log": "Modal trigger failed",
                    })

            background_tasks.add_task(trigger_modal)

        # Return immediately - Modal will update DB when done
        record["status"] = "assembling"
        record["assembly_progress"] = 1
        record["assembly_stage"] = "queued"
        record["assembly_log"] = log_label
        return record

    except HTTPException:
        raise
    except Exception as e:
        print(f"Assembly error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/video/{video_id}/cancel-assembly")
async def cancel_assembly(video_id: str):
    """Cancel a running assembly (UI only; does not stop Modal job)."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")

    try:
        # Check director_videos first, then fallback to old videos table
        result = supabase.table("director_videos").select("*").eq("video_id", video_id).execute()
        if not result.data:
            result = supabase.table("videos").select("*").eq("video_id", video_id).execute()
            if not result.data:
                raise HTTPException(status_code=404, detail="Video not found")

        update = _safe_update_video(video_id, {
            "status": "assembly_canceled",
            "assembly_reason": "Canceled by user",
            "assembly_progress": None,
            "assembly_stage": "canceled",
            "assembly_eta_seconds": None,
            "assembly_elapsed_seconds": None,
            "assembly_completed_at": datetime.now(timezone.utc).isoformat(),
            "assembly_log": "Assembly canceled by user",
        })

        if update and update.data:
            return update.data[0]

        # Refresh from correct table
        refreshed = supabase.table("director_videos").select("*").eq("video_id", video_id).execute()
        if not refreshed.data:
            refreshed = supabase.table("videos").select("*").eq("video_id", video_id).execute()
        if refreshed.data:
            return refreshed.data[0]
        raise HTTPException(status_code=500, detail="Failed to cancel assembly")

    except HTTPException:
        raise
    except Exception as e:
        print(f"Cancel error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/videos")
async def list_videos(user_id: str = "demo_user"):
    """List generated videos for a user"""
    # Get videos from new director_videos table
    director_result = supabase.table("director_videos").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(25).execute()
    director_videos = director_result.data or []

    # Get videos from old videos table for backward compatibility
    try:
        old_result = supabase.table("videos").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(25).execute()
        old_videos = old_result.data or []
    except:
        old_videos = []

    # Combine and sort by created_at, limit to 25
    all_videos = director_videos + old_videos
    all_videos.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return [_maybe_reconcile_video(record) for record in all_videos[:25]]


@app.delete("/api/video/{video_id}")
async def delete_video(video_id: str):
    """Delete a video"""
    # Try deleting from director_videos first
    result = supabase.table("director_videos").delete().eq("video_id", video_id).execute()
    if result.data:
        return {"status": "deleted", "video_id": video_id}

    # Fallback to old videos table
    result = supabase.table("videos").delete().eq("video_id", video_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Video not found")
    return {"success": True, "message": "Video deleted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
