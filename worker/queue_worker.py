import os
import time
import uuid
from datetime import datetime, timedelta, timezone

from supabase import create_client

from viral_pipeline import assemble_video


SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
WORKER_ID = os.environ.get("WORKER_ID") or f"assembly-worker-{uuid.uuid4().hex[:8]}"
POLL_SECONDS = int(os.environ.get("ASSEMBLY_POLL_SECONDS", "5"))
LOCK_SECONDS = int(os.environ.get("ASSEMBLY_LOCK_SECONDS", "900"))
RETRY_BACKOFF_SECONDS = int(os.environ.get("ASSEMBLY_RETRY_BACKOFF_SECONDS", "120"))
WORKER_MODE = os.environ.get("WORKER_MODE", "service").lower()
MAX_RUNTIME_SECONDS = int(os.environ.get("WORKER_MAX_SECONDS", "0"))
MAX_JOBS = int(os.environ.get("WORKER_MAX_JOBS", "0"))


def log(message: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    print(f"[{now}] {message}", flush=True)


def update_job(supabase, job_id: str, fields: dict) -> None:
    if "updated_at" not in fields:
        fields = {**fields, "updated_at": datetime.now(timezone.utc).isoformat()}
    supabase.table("assembly_jobs").update(fields).eq("id", job_id).execute()


def claim_job(supabase):
    try:
        result = supabase.rpc("claim_assembly_job", {"worker_id": WORKER_ID, "lock_seconds": LOCK_SECONDS}).execute()
        if result.data:
            return result.data[0]
    except Exception as e:
        log(f"Claim failed: {type(e).__name__}: {e}")
        import traceback
        log(f"Traceback: {traceback.format_exc()}")
    return None


def should_cancel(supabase, video_id: str) -> bool:
    try:
        current = supabase.table("videos").select("status").eq("video_id", video_id).execute()
        if current.data and current.data[0].get("status") == "assembly_canceled":
            return True
    except Exception as e:
        log(f"Cancel check failed: {e}")
    return False


def run_job(supabase, job: dict) -> None:
    job_id = job.get("id")
    video_id = job.get("video_id")
    source_type = job.get("source_type", "director")
    source_id = job.get("source_id")
    payload = job.get("payload") or {}
    attempts = int(job.get("attempts") or 0)
    max_attempts = int(job.get("max_attempts") or 3)

    if not job_id or not video_id:
        return

    if should_cancel(supabase, video_id):
        update_job(supabase, job_id, {"status": "canceled"})
        return

    update_job(supabase, job_id, {"status": "running", "locked_by": WORKER_ID, "locked_at": datetime.now(timezone.utc).isoformat()})

    # Fetch video data from database if payload is empty
    if not payload or not payload.get("image_urls"):
        try:
            # Determine which table to query based on source_type
            table_name = "director_videos" if source_type == "director" else "episodes"
            log(f"Fetching data from {table_name} for video_id: {video_id}")

            video_data = supabase.table(table_name).select("*").eq("video_id", video_id).execute()
            if video_data.data and len(video_data.data) > 0:
                video = video_data.data[0]
                script = video.get("script") or {}
                config = video.get("config") or {}

                # Build payload from video data
                payload = {
                    "video_id": video_id,
                    "image_urls": video.get("image_urls") or [],
                    "audio_url": video.get("audio_url"),
                    "beats": script.get("beats") or [],
                    "durations": [b.get("duration", 4.0) for b in script.get("beats", [])],
                    "include_captions": config.get("include_captions", True),
                    "caption_style": config.get("caption_style", "red_highlight"),
                    "motion_effect": config.get("motion_effect", "ken_burns"),
                    "transition_style": config.get("transition_style", "random"),
                    "color_grade": config.get("color_grade", "cinematic"),
                    "words_per_line": config.get("words_per_line", 2),
                }
                log(f"Built payload with {len(payload.get('beats', []))} beats, captions={payload.get('include_captions')}, style={payload.get('caption_style')}")
            else:
                log(f"No video found in {table_name} for video_id: {video_id}")
                update_job(supabase, job_id, {
                    "status": "failed",
                    "last_error": f"Video not found in {table_name}",
                })
                return
        except Exception as e:
            log(f"Failed to fetch video data: {e}")
            update_job(supabase, job_id, {
                "status": "failed",
                "last_error": f"Failed to fetch video data: {str(e)}",
            })
            return
    else:
        # Ensure video_id is in payload
        payload = {**payload, "video_id": video_id}

    result = assemble_video(payload)

    if result.get("error"):
        attempts += 1
        if attempts >= max_attempts:
            update_job(supabase, job_id, {
                "status": "failed",
                "attempts": attempts,
                "last_error": result.get("error"),
            })
            return

        backoff = RETRY_BACKOFF_SECONDS * attempts
        update_job(supabase, job_id, {
            "status": "retry",
            "attempts": attempts,
            "last_error": result.get("error"),
            "next_run_at": (datetime.now(timezone.utc) + timedelta(seconds=backoff)).isoformat(),
        })
        return

    update_job(supabase, job_id, {
        "status": "completed",
        "attempts": attempts,
    })


def main() -> None:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set")

    log(f"Supabase URL: {SUPABASE_URL}")
    log(f"Supabase KEY prefix: {SUPABASE_KEY[:20]}..." if SUPABASE_KEY else "None")

    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        log(f"Worker started: {WORKER_ID}")
    except Exception as e:
        log(f"FATAL: Failed to create Supabase client: {e}")
        import traceback
        log(f"Traceback: {traceback.format_exc()}")
        raise

    start_time = time.monotonic()
    processed = 0

    log("Entering main loop...")
    while True:
        log(f"Loop iteration - processed: {processed}, runtime: {int(time.monotonic() - start_time)}s")
        if MAX_RUNTIME_SECONDS and (time.monotonic() - start_time) >= MAX_RUNTIME_SECONDS:
            log("Max runtime reached, exiting")
            break
        if MAX_JOBS and processed >= MAX_JOBS:
            log("Max jobs reached, exiting")
            break
        log("Attempting to claim job...")
        job = claim_job(supabase)
        log(f"Claim result: {job}")
        if not job:
            if WORKER_MODE == "job":
                log("No jobs available, exiting")
                break
            time.sleep(POLL_SECONDS)
            continue
        try:
            run_job(supabase, job)
            processed += 1
        except Exception as e:
            log(f"Job {job.get('id')} failed: {e}")
            try:
                update_job(supabase, job.get("id"), {
                    "status": "retry",
                    "attempts": (job.get("attempts") or 0) + 1,
                    "last_error": str(e),
                    "next_run_at": (datetime.now(timezone.utc) + timedelta(seconds=RETRY_BACKOFF_SECONDS)).isoformat(),
                })
            except Exception as inner:
                log(f"Failed to update job status: {inner}")


if __name__ == "__main__":
    main()
