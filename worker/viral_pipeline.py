import os
import random
import re
import shlex
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import httpx
import imageio_ffmpeg
from mutagen import File as MutagenFile
from supabase import create_client

from captions import STYLES as CAPTION_STYLES


TRANSITIONS = [
    "fade",  # Simple cross-fade only
]

COLOR_GRADES = {
    "cinematic": "",
    "vintage": "",
    "vibrant": "",
    "dark": "",
    "neon": "",
    "none": "",
}

def _get_ffmpeg_bin() -> str:
    try:
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def _format_ass_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}".replace(".", ",")


def build_word_by_word_captions(
    beats: List[dict],
    durations: List[float],
    style: str,
    out_path: Path,
    words_per_line: int = 2,
) -> Path:
    """
    Build TikTok-style captions: 1-2 words shown at once, with color highlight on current word.
    Matches the pattern: center-aligned, word-by-word color animation.
    """
    style_def = CAPTION_STYLES.get(style, CAPTION_STYLES["red_highlight"])
    header = style_def["header"]
    highlight_color = style_def.get("highlight_color", "\\c&H0000FFFF&")  # Yellow
    normal_color = style_def.get("normal_color", "\\c&H00FFFFFF&")  # White
    highlight_extra = style_def.get("highlight_extra", "")
    words_per_line = style_def.get("words_per_line", words_per_line)
    use_box_style = style_def.get("use_box_style", False)

    lines = [header]
    cursor = 0.0

    for beat, dur in zip(beats, durations):
        text = (beat.get("line") or "").strip()
        if not text:
            cursor += float(dur)
            continue

        words = [w.strip() for w in text.split() if w.strip()]
        if not words:
            cursor += float(dur)
            continue

        word_duration = float(dur) / len(words)
        word_duration = max(0.3, min(word_duration, 1.0))

        # Group words into chunks (e.g., 2 words at a time)
        for chunk_start in range(0, len(words), words_per_line):
            chunk = words[chunk_start:chunk_start + words_per_line]

            # For each word in the chunk, create a subtitle showing the whole chunk
            # but highlighting only the current word
            for local_idx, current_word in enumerate(chunk):
                global_idx = chunk_start + local_idx
                word_start = cursor + (global_idx * word_duration)
                word_end = word_start + word_duration

                # Build display text: show all words in chunk, highlight current one
                display_parts = []
                for j, word in enumerate(chunk):
                    clean = word.strip('.,!?;:\"').upper()
                    if not clean:
                        continue

                    if j == local_idx:
                        # Current word - highlighted with color and scale
                        anim = "{\\t(0,80,\\fscx110\\fscy110)\\t(80,160,\\fscx100\\fscy100)}"
                        display_parts.append(f"{{{highlight_color}{highlight_extra}}}{anim}{clean}{{\\r}}")
                    else:
                        # Other words - normal color
                        display_parts.append(f"{{{normal_color}}}{clean}{{\\r}}")

                display_text = " ".join(display_parts)

                lines.append(
                    f"Dialogue: 0,{_format_ass_time(word_start)},{_format_ass_time(word_end)},Default,,0,0,0,,{display_text}"
                )

        cursor += float(dur)

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[captions] Generated {len(lines)-1} TikTok-style caption events")
    return out_path


def _enhanced_motion_filter(duration: float, effect: str, scene_index: int) -> str:
    # Use simple, fast filters that don't require zoompan
    # This is much more reliable and won't crash FFmpeg
    base = "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,fps=30"

    # For now, just use the simple base filter without motion effects
    # This ensures stability and fast processing
    return base


def _audio_duration_seconds(audio_path: Path) -> Optional[float]:
    try:
        audio = MutagenFile(str(audio_path))
        if audio and audio.info:
            return float(audio.info.length)
    except Exception:
        return None
    return None


def assemble_video(payload: dict) -> dict:
    video_id = payload.get("video_id")
    image_urls = payload.get("image_urls") or []
    audio_url = payload.get("audio_url")
    beats = payload.get("beats") or []
    durations = payload.get("durations") or []
    include_captions = payload.get("include_captions", True)
    caption_style = payload.get("caption_style", "red_highlight")
    motion_effect = payload.get("motion_effect", "ken_burns")
    transition_style = payload.get("transition_style", "random")
    color_grade = payload.get("color_grade", "cinematic")
    bgm_url = payload.get("bgm_url")
    words_per_line = payload.get("words_per_line", 2)

    if not video_id:
        return {"error": "Missing video_id"}

    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    supabase = None
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
            print(f"[{video_id}] WARN: Supabase client init failed: {e}", flush=True)

    def safe_update(fields: dict):
        if not supabase:
            return None
        if "updated_at" not in fields:
            fields = {**fields, "updated_at": datetime.now(timezone.utc).isoformat()}
        pending = dict(fields)
        attempts = 0
        missing_column_re = re.compile(r"Could not find the '([^']+)' column")
        while True:
            try:
                return supabase.table("videos").update(pending).eq("video_id", video_id).execute()
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
                    return supabase.table("videos").update(trimmed).eq("video_id", video_id).execute()
                raise

    start_time = time.monotonic()
    started_at = datetime.now(timezone.utc).isoformat()
    total_steps = 8
    last_cancel_check = 0.0
    canceled = False

    def check_canceled() -> bool:
        nonlocal canceled, last_cancel_check
        if canceled or not supabase:
            return canceled
        now = time.monotonic()
        if now - last_cancel_check < 5:
            return canceled
        last_cancel_check = now
        try:
            current = supabase.table("videos").select("status").eq("video_id", video_id).execute()
            if current.data and current.data[0].get("status") == "assembly_canceled":
                canceled = True
        except Exception as status_err:
            print(f"[{video_id}] WARN: Status check failed: {status_err}", flush=True)
        return canceled

    def estimate_eta(completed_steps: int) -> Optional[int]:
        if completed_steps <= 0:
            return None
        elapsed = time.monotonic() - start_time
        estimated_total = elapsed / completed_steps * total_steps
        return max(0, int(estimated_total - elapsed))

    def report_status(
        stage: str,
        progress: Optional[int] = None,
        log_line: Optional[str] = None,
        status: Optional[str] = None,
        video_url: Optional[str] = None,
        reason: Optional[str] = None,
        completed_steps: int = 0,
        eta_override: Optional[int] = None,
        completed_at: Optional[str] = None,
    ) -> None:
        canceled_now = check_canceled()
        if canceled_now and not video_url:
            return

        elapsed = int(time.monotonic() - start_time)
        eta_seconds = eta_override if eta_override is not None else estimate_eta(completed_steps)
        effective_status = status or "assembling"
        if progress is None:
            progress = 100 if effective_status == "completed" else max(1, min(99, int((completed_steps / total_steps) * 100)))

        if supabase:
            update_fields = {
                "status": effective_status,
                "assembly_progress": progress,
                "assembly_stage": stage,
                "assembly_eta_seconds": eta_seconds,
                "assembly_elapsed_seconds": elapsed,
                "assembly_started_at": started_at,
            }
            if log_line:
                update_fields["assembly_log"] = log_line
            if video_url:
                update_fields["video_url"] = video_url
            if reason:
                update_fields["assembly_reason"] = reason
            if completed_at:
                update_fields["assembly_completed_at"] = completed_at
            safe_update(update_fields)

    def report_step(step_index: int, stage: str, log_line: str) -> None:
        completed_steps = max(step_index - 1, 0)
        progress = max(1, min(99, int((completed_steps / total_steps) * 100)))
        report_status(
            stage=stage,
            progress=progress,
            log_line=log_line,
            status="assembling",
            completed_steps=completed_steps,
        )

    def fail(reason: str):
        report_status(
            stage="failed",
            status="assembly_failed",
            reason=reason,
            log_line=f"Assembly failed: {reason}",
            completed_steps=total_steps,
        )
        return {"error": reason}

    report_status(stage="starting", progress=1, log_line="Assembly started", status="assembling")

    if not image_urls:
        return fail("No image URLs provided")
    if not audio_url:
        return fail("No audio URL provided")

    ffmpeg_bin = _get_ffmpeg_bin()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        report_step(1, "downloading_images", f"Downloading {len(image_urls)} images")
        image_paths = []
        for i, url in enumerate(image_urls):
            try:
                resp = httpx.get(url, timeout=60.0, follow_redirects=True)
                resp.raise_for_status()
                img_path = tmpdir / f"img_{i:03d}.png"
                img_path.write_bytes(resp.content)
                image_paths.append(img_path)
            except Exception as e:
                return fail(f"Failed to download image {i+1}: {e}")

        report_step(2, "downloading_audio", "Downloading voiceover")
        try:
            resp = httpx.get(audio_url, timeout=60.0, follow_redirects=True)
            resp.raise_for_status()
            audio_path = tmpdir / "voiceover.mp3"
            audio_path.write_bytes(resp.content)
        except Exception as e:
            return fail(f"Failed to download audio: {e}")

        actual_audio_duration = _audio_duration_seconds(audio_path)

        if durations and len(durations) == len(image_urls):
            durations = [float(d) for d in durations]
        elif beats and len(beats) == len(image_urls):
            durations = [float(b.get("duration", 2.5)) for b in beats]
        elif actual_audio_duration:
            avg_duration = actual_audio_duration / len(image_urls)
            durations = [avg_duration] * len(image_urls)
        else:
            durations = [2.5] * len(image_urls)

        total_video_duration = sum(durations)
        if actual_audio_duration:
            duration_diff = abs(total_video_duration - actual_audio_duration)
            if duration_diff > 0.5:
                scale_factor = actual_audio_duration / total_video_duration
                durations = [d * scale_factor for d in durations]

        bgm_path = None
        if bgm_url:
            report_step(3, "downloading_bgm", "Downloading background music")
            try:
                resp = httpx.get(bgm_url, timeout=60.0, follow_redirects=True)
                resp.raise_for_status()
                bgm_path = tmpdir / "bgm.mp3"
                bgm_path.write_bytes(resp.content)
            except Exception:
                bgm_path = None

        report_step(4, "building_motion_clips", "Building motion clips")
        segment_paths: List[Path] = []
        grade_filter = COLOR_GRADES.get(color_grade, COLOR_GRADES["cinematic"])

        for i, (img_path, duration) in enumerate(zip(image_paths, durations)):
            seg_path = tmpdir / f"seg_{i:03d}.mp4"
            motion_vf = _enhanced_motion_filter(duration, motion_effect, i)
            vf = f"{motion_vf},{grade_filter}" if grade_filter else motion_vf

            cmd = [
                ffmpeg_bin, "-y",
                "-loop", "1",
                "-t", str(duration),
                "-i", str(img_path),
                "-vf", vf,
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "28",
                "-r", "30",
                "-threads", "0",
                "-pix_fmt", "yuv420p",
                "-an",
                str(seg_path),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                return fail(f"Segment {i} failed: {result.stderr[:200]}")
            segment_paths.append(seg_path)

        report_step(5, "joining_clips", "Joining video clips")
        if len(segment_paths) == 1:
            video_only = segment_paths[0]
        else:
            # Direct concatenation without any transitions - simple frame cuts for storytelling
            seg_list = tmpdir / "segments.txt"
            seg_list.write_text("\n".join([f"file '{p}'" for p in segment_paths]), encoding="utf-8")
            video_only = tmpdir / "video_concat.mp4"
            concat_cmd = [
                ffmpeg_bin, "-y", "-f", "concat", "-safe", "0",
                "-i", str(seg_list), "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
                "-pix_fmt", "yuv420p", "-r", "30", str(video_only),
            ]
            result = subprocess.run(concat_cmd, capture_output=True, text=True, timeout=240)
            if result.returncode != 0:
                return fail(f"Concat failed: {result.stderr[:240]}")

        report_step(6, "mixing_audio", "Mixing audio")
        final_audio = tmpdir / "final_audio.mp3"
        if bgm_path and bgm_path.exists():
            mix_cmd = [
                ffmpeg_bin, "-y",
                "-i", str(audio_path),
                "-i", str(bgm_path),
                "-filter_complex",
                "[1:a]volume=0.2[bgm];[0:a][bgm]amerge=inputs=2,pan=stereo|c0<c0+c2|c1<c1+c3[aout]",
                "-map", "[aout]",
                "-c:a", "aac",
                "-b:a", "192k",
                str(final_audio),
            ]
            result = subprocess.run(mix_cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                final_audio = audio_path
        else:
            final_audio = audio_path

        report_step(7, "merging_audio_video", "Merging video with audio")
        merged_path = tmpdir / "merged.mp4"
        merge_cmd = [
            ffmpeg_bin, "-y",
            "-i", str(video_only),
            "-i", str(final_audio),
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(merged_path),
        ]
        result = subprocess.run(merge_cmd, capture_output=True, text=True, timeout=240)
        if result.returncode != 0:
            return fail(f"Audio merge failed: {result.stderr[:240]}")

        final_path = merged_path
        print(f"[viral_pipeline] Caption check: include_captions={include_captions}, beats={len(beats) if beats else 0}, caption_style={caption_style}")
        if include_captions and beats:
            report_step(8, "burning_captions", "Adding word-by-word captions")
            ass_path = tmpdir / "captions.ass"
            try:
                print(f"[viral_pipeline] Building captions: style={caption_style}, beats={len(beats)}, words_per_line={words_per_line}")
                build_word_by_word_captions(beats, durations, caption_style, ass_path, words_per_line)
                print(f"[viral_pipeline] Caption file created: {ass_path}, exists={ass_path.exists()}, size={ass_path.stat().st_size if ass_path.exists() else 0} bytes")

                # Use absolute path and proper escaping for subtitles filter
                ass_abs_path = str(ass_path.absolute()).replace('\\', '/').replace(':', '\\:')
                burn_cmd = [
                    ffmpeg_bin, "-y",
                    "-i", str(merged_path),
                    "-vf", f"subtitles={ass_abs_path}:force_style='FontName=Montserrat Black,FontSize=80'",
                    "-c:v", "libx264",
                    "-preset", "fast",
                    "-crf", "23",
                    "-c:a", "copy",
                    "-pix_fmt", "yuv420p",
                    "-r", "30",
                    str(tmpdir / "final.mp4"),
                ]
                print(f"[viral_pipeline] Running caption burn command with subtitles filter...")
                print(f"[viral_pipeline] ASS path: {ass_abs_path}")
                result = subprocess.run(burn_cmd, capture_output=True, text=True, timeout=180)
                if result.returncode == 0:
                    final_path = tmpdir / "final.mp4"
                    print(f"[viral_pipeline] Captions burned successfully!")
                else:
                    print(f"[viral_pipeline] Caption burn FAILED!")
                    print(f"[viral_pipeline] Error: {result.stderr[:1000]}")
            except Exception as e:
                print(f"[viral_pipeline] Caption error: {type(e).__name__}: {e}")
                import traceback
                print(f"[viral_pipeline] Traceback: {traceback.format_exc()}")
        else:
            report_step(8, "finalizing", "Finalizing video")

        if not supabase:
            return fail("Supabase not configured")

        report_status(stage="uploading_video", progress=95, log_line="Uploading video")
        storage_path = f"{video_id}/video.mp4"
        try:
            supabase.storage.from_("videos").upload(
                storage_path,
                str(final_path),
                {"content-type": "video/mp4", "upsert": "true"},
            )
        except Exception as upload_err:
            return fail(f"Upload failed: {upload_err}")

        video_url = supabase.storage.from_("videos").get_public_url(storage_path)
        if video_url.endswith("?"):
            video_url = video_url[:-1]

        completed_at = datetime.now(timezone.utc).isoformat()
        report_status(
            stage="completed",
            progress=100,
            status="completed",
            video_url=video_url,
            log_line="Assembly completed",
            completed_steps=total_steps,
            eta_override=0,
            completed_at=completed_at,
        )
        return {
            "video_url": video_url,
            "duration": sum(durations),
        }
