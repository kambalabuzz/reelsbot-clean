"""
Video generation engine with queue-based FFmpeg assembly.

Assembly runs in a background worker pulling from the Supabase queue.
Modal is optional (set ASSEMBLY_BACKEND=modal if you still use it).

Architecture:
1. Render API - script generation, image generation, voiceover
2. Render worker - FFmpeg assembly (queue)
3. Supabase - storage + job queue
"""

import json
import gc
import os
import uuid
import time
import asyncio
import tempfile
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List, Callable, Tuple, Union

import httpx
import imageio_ffmpeg
from openai import OpenAI
from supabase import create_client
from PIL import Image, ImageDraw, ImageFont

# Environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN")
MODAL_TOKEN_ID = os.environ.get("MODAL_TOKEN_ID")
MODAL_TOKEN_SECRET = os.environ.get("MODAL_TOKEN_SECRET")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Initialize clients
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

VIDEO_BUCKET = "videos"
PLACEHOLDER_BG = (26, 26, 46)
PLACEHOLDER_TEXT = (255, 255, 255)

# Voice mappings
OPENAI_VOICES = {
    "adam": "onyx",
    "john": "echo", 
    "marcus": "fable",
    "alex": "alloy",
    "sarah": "nova",
    "emma": "shimmer",
}

# Utilities
async def download_bytes(url: str) -> bytes:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content


def create_placeholder_image(text: str, width: int = 1080, height: int = 1920) -> bytes:
    img = Image.new("RGB", (width, height), PLACEHOLDER_BG)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("LiberationSans-Bold.ttf", 56)
    except Exception:
        font = ImageFont.load_default()
    wrapped = "\n".join([text[i:i+24] for i in range(0, len(text), 24)]) or "Scene"
    w, h = draw.multiline_textsize(wrapped, font=font)
    draw.multiline_text(((width - w) / 2, height / 2 - h), wrapped, font=font, fill=PLACEHOLDER_TEXT, align="center")
    buf = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    img.save(buf.name, format="JPEG", quality=90)
    data = Path(buf.name).read_bytes()
    Path(buf.name).unlink(missing_ok=True)
    return data


def upload_bytes(path: str, data: bytes, content_type: str) -> Optional[str]:
    if not supabase:
        return None
    try:
        supabase.storage.from_(VIDEO_BUCKET).upload(path, data, {"content-type": content_type, "upsert": True})
        return supabase.storage.from_(VIDEO_BUCKET).get_public_url(path)
    except Exception as e:
        print(f"[upload] Failed to upload {path}: {e}")
        return None

ELEVENLABS_VOICES = {
    "adam": "pNInz6obpgDQGcFmaJgB",
    "rachel": "21m00Tcm4TlvDq8ikWAM",
    "josh": "TxGEqnHWrfWFTfGW9XjX",
    "bella": "EXAVITQu4vr4xnSDxMaL",
}

ART_STYLES = {
    "cinematic": "Cinematic film still, dramatic lighting, movie scene, 8K quality, photorealistic",
    "anime": "Anime style illustration, vibrant colors, Studio Ghibli inspired, detailed",
    "comic": "Dark comic book style, high contrast, dramatic shadows, graphic novel aesthetic",
    "realistic": "Hyperrealistic photograph, DSLR quality, sharp focus, professional lighting",
    "horror": "Dark horror aesthetic, unsettling atmosphere, creepy lighting, ominous mood",
    "cyberpunk": "Cyberpunk style, neon lights, futuristic city, rain-soaked streets, blade runner aesthetic",
}


def ensure_bucket():
    if not supabase:
        return
    try:
        supabase.storage.create_bucket(VIDEO_BUCKET, {"public": True})
    except:
        pass


def upload_to_storage(path: str, data: Union[bytes, str, Path], content_type: str) -> Optional[str]:
    if not supabase:
        return None
    try:
        supabase.storage.from_(VIDEO_BUCKET).upload(path, data, {"content-type": content_type, "upsert": "true"})
        url = supabase.storage.from_(VIDEO_BUCKET).get_public_url(path)
        if url and url.endswith('?'):
            url = url[:-1]
        return url
    except Exception as e:
        print(f"[storage] Upload failed: {e}")
        return None


async def download_bytes(url: str) -> bytes:
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
    return resp.content


def _download_bytes_sync(url: str, timeout: float = 60.0) -> bytes:
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.content


def _download_file_sync(url: str, dest: Path, timeout: float = 60.0) -> None:
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        with client.stream("GET", url) as resp:
            resp.raise_for_status()
            with dest.open("wb") as handle:
                for chunk in resp.iter_bytes():
                    handle.write(chunk)


# ============ SCRIPT GENERATION ============

async def generate_script(topic: str, niche: str = "entertainment", beats: int = 8) -> dict:
    if not openai_client:
        raise RuntimeError("OpenAI API key not configured")

    prompt = f"""Create a viral short-form vertical video script about: {topic}
    Niche: {niche}

    Requirements:
    - Generate exactly {beats} beats.
    - Each beat must include natural visual direction that can map to a single image.
    - Keep narration tight and vivid. Avoid platform handles, watermarks or on-screen text.
    - Provide a realistic duration per beat (3.5-5.5 seconds) that sums to 32-50 seconds total.

    Return JSON:
    {{
        "title": "Catchy title",
        "hook": "Opening hook (first 3 seconds)",
        "beats": [
            {{
                "line": "Narration text",
                "visual": "Visual description for image generation",
                "duration": 4.2
            }},
            ...
        ],
        "cta": "Call to action",
        "total_duration": 45
    }}
    Ensure durations are numbers, not strings."""

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a viral video scriptwriter. Always respond with valid JSON."},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
    )

    return json.loads(response.choices[0].message.content)


# ============ VOICEOVER ============

async def generate_voiceover_openai(text: str, voice: str = "alloy") -> bytes:
    if not openai_client:
        raise RuntimeError("OpenAI not configured")
    
    valid_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    if voice not in valid_voices:
        voice = "alloy"
    
    response = openai_client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text,
    )
    return response.content


async def generate_voiceover_elevenlabs(text: str, voice_id: str) -> bytes:
    if not ELEVENLABS_API_KEY:
        raise RuntimeError("ElevenLabs not configured")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": ELEVENLABS_API_KEY,
            },
            json={
                "text": text,
                "model_id": "eleven_turbo_v2_5",
                "voice_settings": {
                    "stability": 0.4,
                    "similarity_boost": 0.85,
                    "style": 0.3,
                    "use_speaker_boost": True
                },
            },
        )
        response.raise_for_status()
        return response.content


async def generate_voiceover(text: str, voice: str = "adam") -> bytes:
    if ELEVENLABS_API_KEY and voice in ELEVENLABS_VOICES:
        try:
            print(f"[voice] Using ElevenLabs: {voice}")
            return await generate_voiceover_elevenlabs(text, ELEVENLABS_VOICES[voice])
        except Exception as e:
            print(f"[voice] ElevenLabs failed: {e}")
    
    openai_voice = OPENAI_VOICES.get(voice, "alloy")
    print(f"[voice] Using OpenAI: {openai_voice}")
    return await generate_voiceover_openai(text, openai_voice)


# ============ IMAGE GENERATION ============

async def generate_image_replicate(prompt: str, style: str = "cinematic") -> Optional[str]:
    if not REPLICATE_API_TOKEN:
        return None

    try:
        import replicate

        style_prompt = ART_STYLES.get(style, ART_STYLES["cinematic"])
        # Enhanced prompt with people-focused elements for TikTok virality
        full_prompt = (
            f"{style_prompt}. Vertical 9:16 format, featuring people or human subjects in engaging dynamic scenes. "
            f"{prompt}. With visible people, human faces, emotional expressions, vibrant and engaging composition. "
            "Ultra clean frame, cinematic composition, no text overlays, no resolution labels, no watermarks, no logos."
        )
        
        def run_once():
            return replicate.run(
                "black-forest-labs/flux-schnell",
                input={
                    "prompt": full_prompt,
                    "negative_prompt": "text, watermark, logo, caption, words, signature, blurry",
                    "aspect_ratio": "9:16",
                    "num_outputs": 1,
                    "output_format": "webp",
                    "output_quality": 90,
                },
            )

        try:
            output = run_once()
        except Exception as e:
            msg = str(e)
            if "429" in msg or "rate limit" in msg.lower():
                print("[image] Replicate 429, retrying after 10s...")
                time.sleep(10)
                output = run_once()
            else:
                raise
        
        if output is None:
            return None
        
        if isinstance(output, list):
            if len(output) == 0:
                return None
            result = output[0]
        else:
            result = output
        
        if hasattr(result, 'url'):
            return str(result.url)
        if isinstance(result, str):
            return result
            
        return None
            
    except Exception as e:
        print(f"[image] Replicate error: {e}")
        return None


async def generate_image_dalle(prompt: str, style: str = "cinematic") -> str:
    if not openai_client:
        raise RuntimeError("OpenAI not configured")

    style_prompt = ART_STYLES.get(style, ART_STYLES["cinematic"])

    # Enhanced prompt with people-focused elements for TikTok virality
    base_prompt = (
        f"{style_prompt}. Vertical 9:16 format, featuring people or human subjects in engaging dynamic scenes. "
        f"{prompt}. With visible people, human faces, emotional expressions, vibrant and engaging composition. "
        "Crisp lighting, storytelling focus. No text, no watermark, no logo, no resolution labels."
    )

    try:
        response = openai_client.images.generate(
            model="dall-e-3",
            prompt=base_prompt,
            size="1024x1792",  # Portrait 9:16 format (TikTok optimized)
            quality="standard",
            n=1,
        )
        return response.data[0].url
    except Exception as e:
        msg = str(e)
        if "content_policy" in msg or "safety" in msg.lower():
            # Fallback to safer prompt without reducing people focus
            safe_prompt = (
                f"{style_prompt}. PG-13, safe for work, featuring people in friendly engaging scenes. "
                f"{prompt}. With human subjects, positive emotions, welcoming composition. "
                "Vertical 9:16 format, no violence, no gore. No text, no watermarks."
            )
            response = openai_client.images.generate(
                model="dall-e-3",
                prompt=safe_prompt,
                size="1024x1792",
                quality="standard",
                n=1,
            )
            return response.data[0].url
        raise


async def generate_image(prompt: str, style: str = "cinematic") -> str:
    if REPLICATE_API_TOKEN:
        img_url = await generate_image_replicate(prompt, style)
        if img_url:
            return img_url
        print(f"[image] Replicate failed, trying DALL-E")
    
    return await generate_image_dalle(prompt, style)


# ============ VIDEO ASSEMBLY (Modal) ============

async def assemble_video_modal(
    video_id: str,
    image_urls: List[str],
    audio_url: str,
    beats: List[dict],
    caption_style: str = "red_highlight",
    motion_effect: str = "ken_burns",
    transition_style: str = "random",
    color_grade: str = "cinematic",
    bgm_url: Optional[str] = None,
    words_per_line: int = 2,
    callback_url: Optional[str] = None,
    callback_token: Optional[str] = None,
) -> Optional[str]:
    """
    Call Modal webhook to assemble VIRAL video V2 using FFmpeg.
    NOW WITH:
    - Word-by-word animated captions (like viral TikTok videos)
    - Background music mixing
    - Dynamic transitions and color grading
    - No gaps between words (<1 sec timing)
    """
    # Modal webhook URL - you'll deploy this separately
    MODAL_WEBHOOK_URL = os.environ.get("MODAL_WEBHOOK_URL")

    if not MODAL_WEBHOOK_URL:
        print(f"[{video_id}] Modal webhook URL not configured")
        return None

    print(f"[{video_id}] Calling Modal VIRAL V2 worker for video assembly...")
    print(f"[{video_id}] Effects: motion={motion_effect}, transitions={transition_style}, grade={color_grade}")
    print(f"[{video_id}] Captions: word-by-word ({words_per_line} words/line), style={caption_style}")
    print(f"[{video_id}] BGM: {'Yes' if bgm_url else 'No'}")

    # Calculate durations (will be capped at 3s by Modal worker)
    durations = [float(b.get("duration", 2.5)) for b in beats]

    payload = {
        "video_id": video_id,
        "image_urls": image_urls,
        "audio_url": audio_url,
        "durations": durations,
        "beats": beats,  # For word-by-word captions
        "include_captions": True,
        "caption_style": caption_style,
        "motion_effect": motion_effect,
        "transition_style": transition_style,
        "color_grade": color_grade,
        "bgm_url": bgm_url,  # NEW: Background music
        "words_per_line": words_per_line,  # NEW: 1-2 words at a time
        "output_width": 1080,
        "output_height": 1920,
        "fps": 30,
    }
    if callback_url:
        payload["callback_url"] = callback_url
    if callback_token:
        payload["callback_token"] = callback_token
    
    try:
        async with httpx.AsyncClient(timeout=300.0, follow_redirects=True) as client:  # 5 min timeout
            response = await client.post(
                MODAL_WEBHOOK_URL,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            result = response.json()
            
            video_url = result.get("video_url")
            if video_url:
                print(f"[{video_id}] Modal assembly complete: {video_url}")
                return video_url
            else:
                error = result.get("error", "Unknown error")
                print(f"[{video_id}] Modal error: {error}")
                return None
                
    except Exception as e:
        print(f"[{video_id}] Modal request failed: {e}")
        return None


def _get_ffmpeg_path() -> str:
    try:
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def assemble_video_local_sync(
    video_id: str,
    image_urls: List[str],
    audio_url: str,
    beats: List[dict],
    output_width: int = 720,
    output_height: int = 1280,
    fps: int = 30,
    progress_cb: Optional[Callable[[dict], None]] = None,
    should_cancel: Optional[Callable[[], bool]] = None,
) -> Tuple[Optional[str], Optional[str]]:
    if not image_urls:
        return None, "No image URLs provided"
    if not audio_url:
        return None, "No audio URL provided"

    ffmpeg_bin = _get_ffmpeg_path()
    tmpdir = Path(tempfile.mkdtemp(prefix=f"assemble_{video_id}_"))
    try:
        if progress_cb:
            progress_cb({"stage": "downloading_images", "progress": 10, "log": "Downloading images"})

        image_paths = []
        for idx, url in enumerate(image_urls):
            if should_cancel and should_cancel():
                return None, "Canceled by user"
            img_path = tmpdir / f"img_{idx:03d}.jpg"
            _download_file_sync(url, img_path, timeout=60.0)
            image_paths.append(img_path)

        if progress_cb:
            progress_cb({"stage": "downloading_audio", "progress": 20, "log": "Downloading audio"})

        if should_cancel and should_cancel():
            return None, "Canceled by user"
        audio_path = tmpdir / "audio.mp3"
        _download_file_sync(audio_url, audio_path, timeout=60.0)

        durations = [float(b.get("duration", 4.0)) for b in (beats or [])]
        if len(durations) != len(image_paths):
            durations = [4.0] * len(image_paths)

        if progress_cb:
            progress_cb({"stage": "building_segments", "progress": 40, "log": "Building video segments"})

        segment_paths: List[Path] = []
        for idx, (img_path, duration) in enumerate(zip(image_paths, durations)):
            if should_cancel and should_cancel():
                return None, "Canceled by user"
            seg_path = tmpdir / f"seg_{idx:03d}.mp4"
            cmd = [
                ffmpeg_bin,
                "-y",
                "-loop", "1",
                "-t", str(duration),
                "-i", str(img_path),
                "-vf", f"scale={output_width}:{output_height},format=yuv420p",
                "-r", str(fps),
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "28",
                "-pix_fmt", "yuv420p",
                "-an",
                str(seg_path),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return None, f"Segment {idx} failed: {result.stderr[:200]}"
            segment_paths.append(seg_path)

        if progress_cb:
            progress_cb({"stage": "concatenating", "progress": 70, "log": "Concatenating segments"})

        concat_list = tmpdir / "segments.txt"
        concat_list.write_text("\n".join([f"file '{p}'" for p in segment_paths]), encoding="utf-8")
        video_only = tmpdir / "video_concat.mp4"
        concat_cmd = [
            ffmpeg_bin,
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy",
            str(video_only),
        ]
        concat_result = subprocess.run(concat_cmd, capture_output=True, text=True)
        if concat_result.returncode != 0:
            concat_cmd = [
                ffmpeg_bin,
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_list),
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "28",
                "-pix_fmt", "yuv420p",
                str(video_only),
            ]
            concat_result = subprocess.run(concat_cmd, capture_output=True, text=True)
            if concat_result.returncode != 0:
                return None, f"Concat failed: {concat_result.stderr[:200]}"

        if progress_cb:
            progress_cb({"stage": "muxing_audio", "progress": 85, "log": "Muxing audio"})

        if should_cancel and should_cancel():
            return None, "Canceled by user"
        final_path = tmpdir / "final.mp4"
        mux_cmd = [
            ffmpeg_bin,
            "-y",
            "-i", str(video_only),
            "-i", str(audio_path),
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            str(final_path),
        ]
        mux_result = subprocess.run(mux_cmd, capture_output=True, text=True)
        if mux_result.returncode != 0:
            mux_cmd = [
                ffmpeg_bin,
                "-y",
                "-i", str(video_only),
                "-i", str(audio_path),
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "28",
                "-c:a", "aac",
                "-shortest",
                str(final_path),
            ]
            mux_result = subprocess.run(mux_cmd, capture_output=True, text=True)
            if mux_result.returncode != 0:
                return None, f"Mux failed: {mux_result.stderr[:200]}"

        if progress_cb:
            progress_cb({"stage": "uploading_video", "progress": 95, "log": "Uploading video"})

        video_url = None
        if supabase:
            try:
                video_url = upload_to_storage(f"{video_id}/video.mp4", final_path, "video/mp4")
            except Exception as e:
                return None, f"Upload failed: {e}"

        if progress_cb:
            progress_cb({"stage": "completed", "progress": 100, "log": "Assembly completed"})

        gc.collect()
        return video_url, None
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ============ MAIN VIDEO GENERATION ============

async def generate_video(
    topic: str,
    voice: str = "adam",
    art_style: str = "cinematic",
    niche: str = "entertainment",
    beats_count: int = 8,
    add_music: bool = True,
    music_style: str = "suspense",
    include_captions: bool = True,
    bgm_mode: str = "random",
    bgm_track_id: Optional[str] = None,
    bgm_custom_url: Optional[str] = None,
    assemble: bool = True,
    caption_style: str = "red_highlight",
    motion_effect: str = "ken_burns",
    transition_style: str = "random",
    color_grade: str = "cinematic",
    words_per_line: int = 2,
    callback_url: Optional[str] = None,
    callback_token: Optional[str] = None,
) -> dict:
    """
    Main video generation function V2.
    1. Generate script (GPT-4)
    2. Generate voiceover (ElevenLabs/OpenAI)
    3. Generate images (Replicate/DALL-E)
    4. Assemble VIRAL video V2 (Modal - with word-by-word captions, BGM, transitions, color grading!)
    """
    video_id = str(uuid.uuid4())[:8]
    
    print(f"[{video_id}] === STARTING VIDEO GENERATION ===")
    print(f"[{video_id}] Topic: {topic}")
    
    if not openai_client:
        raise RuntimeError("OpenAI API key required")
    
    ensure_bucket()
    
    # ===== STEP 1: Generate Script =====
    print(f"[{video_id}] Step 1/4: Generating script...")
    script = await generate_script(topic, niche, beats_count)
    print(f"[{video_id}] Script: {script.get('title', 'Untitled')}")
    
    # ===== STEP 2: Generate Voiceover =====
    print(f"[{video_id}] Step 2/4: Generating voiceover...")
    narration = script["hook"] + " " + " ".join([b["line"] for b in script["beats"]]) + " " + script["cta"]
    
    audio_bytes = await generate_voiceover(narration, voice)
    print(f"[{video_id}] Voiceover: {len(audio_bytes)} bytes")
    
    # Upload audio
    audio_url = None
    if supabase:
        audio_url = upload_to_storage(f"{video_id}/audio.mp3", audio_bytes, "audio/mpeg")
        print(f"[{video_id}] Audio uploaded")
    del audio_bytes
    gc.collect()
    
    # ===== STEP 3: Generate Images =====
    print(f"[{video_id}] Step 3/4: Generating {len(script['beats'])} images...")
    image_urls = []
    
    for i, beat in enumerate(script["beats"]):
        try:
            print(f"[{video_id}] Image {i+1}/{len(script['beats'])}...")
            img_url = await generate_image(beat["visual"], art_style)
            
            # Store immediately
            if supabase and img_url:
                try:
                    img_bytes = await download_bytes(img_url)
                    stored_url = upload_to_storage(
                        f"{video_id}/image_{i+1:02d}.webp",
                        img_bytes,
                        "image/webp"
                    )
                    del img_bytes
                    if stored_url:
                        img_url = stored_url
                except Exception as e:
                    print(f"[{video_id}] Image storage failed: {e}")
            
            image_urls.append(img_url)
            
        except Exception as e:
            print(f"[{video_id}] Image {i+1} failed: {e}")
            placeholder_bytes = create_placeholder_image(beat.get("visual", f"Scene {i+1}"))
            stored = upload_to_storage(f"{video_id}/image_{i+1:02d}_placeholder.jpg", placeholder_bytes, "image/jpeg") if supabase else None
            del placeholder_bytes
            image_urls.append(stored or "")
    
    # ===== STEP 4: Assemble Video =====
    video_url = None
    status = "assets_ready"
    assembly_reason = ""
    
    MODAL_WEBHOOK_URL = os.environ.get("MODAL_WEBHOOK_URL")
    assembly_backend = os.environ.get("ASSEMBLY_BACKEND", "queue").lower()
    if assembly_backend == "auto":
        if os.environ.get("ASSEMBLY_QUEUE_ENABLED", "true").lower() != "false":
            assembly_backend = "queue"
        elif MODAL_WEBHOOK_URL:
            assembly_backend = "modal"
        else:
            assembly_backend = "local"

    use_queue = assemble and audio_url and image_urls and assembly_backend == "queue"
    use_modal = (
        assemble
        and MODAL_WEBHOOK_URL
        and audio_url
        and image_urls
        and assembly_backend == "modal"
    )
    use_local = (
        assemble
        and audio_url
        and image_urls
        and assembly_backend == "local"
    )

    if use_queue:
        status = "assembling"
        assembly_reason = "Queued for assembly"

    if use_modal:
        print(f"[{video_id}] Step 4/4: Assembling VIRAL V2 video with Modal...")
        try:
            # Get BGM URL if requested
            bgm_url = None
            if add_music and bgm_custom_url:
                bgm_url = bgm_custom_url
            elif add_music:
                # TODO: Implement BGM selection from library
                print(f"[{video_id}]   BGM: Using custom URL or library (not implemented yet)")

            video_url = await assemble_video_modal(
                video_id=video_id,
                image_urls=image_urls,
                audio_url=audio_url,
                beats=script.get("beats", []),
                caption_style=caption_style,
                motion_effect=motion_effect,
                transition_style=transition_style,
                color_grade=color_grade,
                bgm_url=bgm_url,
                words_per_line=words_per_line,
                callback_url=callback_url,
                callback_token=callback_token,
            )
            
            if video_url:
                # Store final video in Supabase
                if supabase:
                    try:
                        video_bytes = await download_bytes(video_url)
                        stored_url = upload_to_storage(
                            f"{video_id}/video.mp4",
                            video_bytes,
                            "video/mp4"
                        )
                        del video_bytes
                        if stored_url:
                            video_url = stored_url
                    except Exception as e:
                        print(f"[{video_id}] Video storage failed: {e}")
                
                status = "completed"
            else:
                assembly_reason = "Modal assembly failed"
                if assembly_backend == "auto":
                    use_local = True
                
        except Exception as e:
            print(f"[{video_id}] Assembly error: {e}")
            assembly_reason = str(e)
            if assembly_backend == "auto":
                use_local = True

    if use_local and not video_url:
        print(f"[{video_id}] Step 4/4: Assembling video locally (fallback)...")
        try:
            local_url, local_error = await asyncio.to_thread(
                assemble_video_local_sync,
                video_id,
                image_urls,
                audio_url,
                script.get("beats", []),
            )
            if local_url:
                video_url = local_url
                status = "completed"
            else:
                assembly_reason = local_error or "Local assembly failed"
        except Exception as e:
            print(f"[{video_id}] Local assembly error: {e}")
            assembly_reason = str(e)

    if not video_url and not assembly_reason:
        if use_queue:
            assembly_reason = "Queued for assembly"
        elif not MODAL_WEBHOOK_URL and assembly_backend != "local":
            assembly_reason = "Modal not configured - deploy modal_ffmpeg.py first"
        elif not audio_url:
            assembly_reason = "No audio URL"
        elif not assemble:
            assembly_reason = "Assembly disabled"
    
    # ===== RETURN =====
    result = {
        "video_id": video_id,
        "status": status,
        "script": script,
        "audio_url": audio_url,
        "video_url": video_url,
        "image_urls": image_urls,
        "captions_url": None,
        "config": {
            "topic": topic,
            "voice": voice,
            "art_style": art_style,
            "niche": niche,
            "beats_count": beats_count,
            "include_captions": include_captions,
            "caption_style": caption_style,
            "motion_effect": motion_effect,
            "transition_style": transition_style,
            "color_grade": color_grade,
            "words_per_line": words_per_line,
        },
        "message": "Video ready!" if video_url else f"Assets ready. {assembly_reason}",
        "assembly_available": bool(assemble),
        "assembly_reason": assembly_reason,
    }
    
    print(f"[{video_id}] === COMPLETE === Status: {status}")
    gc.collect()
    return result


async def reassemble_video(
    video_record: dict,
    callback_url: Optional[str] = None,
    callback_token: Optional[str] = None,
) -> dict:
    """Re-assemble video using existing assets. Reuses audio if available."""
    if not video_record:
        raise RuntimeError("Video record missing")
    
    video_id = video_record.get("video_id", str(uuid.uuid4())[:8])
    script = video_record.get("script") or {}
    config = video_record.get("config") or {}
    image_urls = video_record.get("image_urls") or []
    existing_audio_url = video_record.get("audio_url")
    
    print(f"[{video_id}] === REASSEMBLING VIDEO ===")
    print(f"[{video_id}] Images: {len(image_urls)}")
    print(f"[{video_id}] Existing audio: {existing_audio_url}")
    
    # Use existing audio URL if available, otherwise regenerate
    audio_url = existing_audio_url
    
    if not audio_url:
        print(f"[{video_id}] No existing audio, regenerating...")
        voice = config.get("voice", "adam")
        beats = script.get("beats", [])
        narration = script.get("hook", "") + " " + " ".join([b.get("line", "") for b in beats]) + " " + script.get("cta", "")
        
        audio_bytes = await generate_voiceover(narration, voice)
        if supabase:
            audio_url = upload_to_storage(f"{video_id}/audio.mp3", audio_bytes, "audio/mpeg")
            print(f"[{video_id}] Audio regenerated: {audio_url}")
    else:
        print(f"[{video_id}] Using existing audio")
    
    # Call Modal (or local fallback) for assembly
    video_url = None
    MODAL_WEBHOOK_URL = os.environ.get("MODAL_WEBHOOK_URL")
    assembly_backend = os.environ.get("ASSEMBLY_BACKEND", "auto").lower()
    use_modal = MODAL_WEBHOOK_URL and audio_url and image_urls and assembly_backend in ("auto", "modal")
    use_local = audio_url and image_urls and (assembly_backend == "local" or (assembly_backend == "auto" and not MODAL_WEBHOOK_URL))

    if use_modal:
        print(f"[{video_id}] Calling Modal VIRAL V2 worker for assembly...")
        beats = script.get("beats", [])
        caption_style = config.get("caption_style", "red_highlight")
        motion_effect = config.get("motion_effect", "ken_burns")
        transition_style = config.get("transition_style", "random")
        color_grade = config.get("color_grade", "cinematic")
        bgm_url = config.get("bgm_url")
        words_per_line = config.get("words_per_line", 2)
        video_url = await assemble_video_modal(
            video_id,
            image_urls,
            audio_url,
            beats,
            caption_style=caption_style,
            motion_effect=motion_effect,
            transition_style=transition_style,
            color_grade=color_grade,
            bgm_url=bgm_url,
            words_per_line=words_per_line,
            callback_url=callback_url,
            callback_token=callback_token,
        )
        
        if video_url:
            print(f"[{video_id}] Assembly successful: {video_url}")
        else:
            print(f"[{video_id}] Assembly failed")
            if assembly_backend == "auto":
                use_local = True

    if use_local and not video_url:
        print(f"[{video_id}] Assembling locally (fallback)...")
        local_url, local_error = await asyncio.to_thread(
            assemble_video_local_sync,
            video_id,
            image_urls,
            audio_url,
            script.get("beats", []),
        )
        if local_url:
            video_url = local_url
            print(f"[{video_id}] Local assembly successful: {video_url}")
        else:
            print(f"[{video_id}] Local assembly failed: {local_error}")

    if not video_url:
        if not MODAL_WEBHOOK_URL and assembly_backend != "local":
            print(f"[{video_id}] Modal not configured")
        if not audio_url:
            print(f"[{video_id}] No audio URL")
        if not image_urls:
            print(f"[{video_id}] No image URLs")
    
    return {
        "status": "completed" if video_url else "assets_ready",
        "video_url": video_url,
        "audio_url": audio_url,
        "config": config,
    }
