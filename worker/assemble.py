# assemble.py
"""
Video assembly with configurable motion effects.
"""

import os
import random
from pathlib import Path

from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    concatenate_videoclips,
    concatenate_audioclips,
    CompositeAudioClip,
    CompositeVideoClip,
    vfx,
)
from PIL import Image

# Pillow 10+ compatibility
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

W, H = 1080, 1920
DEFAULT_FPS = 30


# =============================================================================
# MOTION EFFECTS
# =============================================================================

def _apply_ken_burns(clip: ImageClip, dur: float, idx: int) -> ImageClip:
    """Ken Burns effect: slow zoom/pan."""
    clip = clip.set_duration(dur)
    
    if idx % 3 == 0:
        # Slow zoom in
        clip = clip.fx(vfx.resize, lambda t: 1.02 + 0.04 * (t / dur))
    elif idx % 3 == 1:
        # Slow zoom out
        clip = clip.fx(vfx.resize, lambda t: 1.06 - 0.04 * (t / dur))
    else:
        # Gentle sideways pan + tiny zoom
        clip = clip.set_position(
            lambda t: (int(-25 * (t / dur)), "center")
        ).fx(vfx.resize, lambda t: 1.01 + 0.03 * (t / dur))
    
    return clip


def _apply_static(clip: ImageClip, dur: float, idx: int) -> ImageClip:
    """No motion - static image."""
    return clip.set_duration(dur)


def _apply_zoom_pulse(clip: ImageClip, dur: float, idx: int) -> ImageClip:
    """Rhythmic zoom pulse effect."""
    clip = clip.set_duration(dur)
    
    # Pulse every ~0.5 seconds
    def pulse_scale(t):
        import math
        base = 1.0
        pulse = 0.02 * math.sin(t * 4 * math.pi)  # 2 pulses per second
        return base + pulse
    
    clip = clip.fx(vfx.resize, pulse_scale)
    return clip


def _apply_shake(clip: ImageClip, dur: float, idx: int) -> ImageClip:
    """Subtle handheld shake effect."""
    clip = clip.set_duration(dur)
    
    def shake_position(t):
        import math
        # Subtle random-ish movement
        x = int(3 * math.sin(t * 7) + 2 * math.cos(t * 11))
        y = int(2 * math.sin(t * 9) + 3 * math.cos(t * 5))
        return (x, y)
    
    clip = clip.set_position(shake_position)
    return clip


def _apply_parallax(clip: ImageClip, dur: float, idx: int) -> ImageClip:
    """Parallax-like slow drift effect."""
    clip = clip.set_duration(dur)
    
    direction = idx % 4
    speed = 30  # pixels over duration
    
    if direction == 0:
        # Drift right
        clip = clip.set_position(lambda t: (int(-speed * t / dur), "center"))
    elif direction == 1:
        # Drift left
        clip = clip.set_position(lambda t: (int(speed * t / dur), "center"))
    elif direction == 2:
        # Drift down
        clip = clip.set_position(lambda t: ("center", int(-speed * t / dur)))
    else:
        # Drift up
        clip = clip.set_position(lambda t: ("center", int(speed * t / dur)))
    
    # Add subtle zoom
    clip = clip.fx(vfx.resize, lambda t: 1.02 + 0.02 * (t / dur))
    
    return clip


MOTION_EFFECTS = {
    "ken_burns": _apply_ken_burns,
    "static": _apply_static,
    "zoom_pulse": _apply_zoom_pulse,
    "shake": _apply_shake,
    "parallax": _apply_parallax,
}


# =============================================================================
# IMAGE PREPARATION
# =============================================================================

def _prepare_image(img_path: str, dur: float, idx: int, motion_effect: str = "ken_burns") -> ImageClip:
    """
    Prepare an image clip with proper sizing and motion effect.
    """
    clip = ImageClip(img_path)

    # Fill vertically first
    clip = clip.fx(vfx.resize, height=H)
    w, h = clip.size

    # Center crop to 1080x1920
    if w <= W:
        clip = clip.on_color(size=(W, H), color=(0, 0, 0)).set_position(("center", "center"))
    else:
        x_center = w / 2
        x1 = max(0, x_center - W / 2)
        x2 = x1 + W
        if x2 > w:
            x2 = w
            x1 = w - W
        clip = clip.crop(x1=x1, y1=0, x2=x2, y2=min(h, H))

    # Apply motion effect
    effect_fn = MOTION_EFFECTS.get(motion_effect, _apply_ken_burns)
    clip = effect_fn(clip, dur, idx)

    return clip


# =============================================================================
# MAIN ASSEMBLE
# =============================================================================

def assemble(
    script_text: str,
    audio_path: str,
    bg_paths: list[str],
    cfg_path: str,
    music_dir: str,
    out_path: str,
    lines: list[str],
    motion_effect: str = "ken_burns",
    music_volume: float = 0.10,
    voice_volume: float = 1.12,
):
    """
    Build base reel (images + voice + music).
    
    Args:
        script_text: Full narration text
        audio_path: Path to voice audio file
        bg_paths: List of image paths for backgrounds
        cfg_path: Path to template config (unused currently)
        music_dir: Directory containing music files
        out_path: Output video path
        lines: List of narration lines (for timing)
        motion_effect: Motion effect to apply ("ken_burns", "static", etc.)
        music_volume: Background music volume (0.0 - 1.0)
        voice_volume: Voice volume multiplier
    """
    out_path = str(out_path)
    Path(os.path.dirname(out_path)).mkdir(parents=True, exist_ok=True)

    # Load narration audio
    print("[assemble] Loading narration audio…")
    voice = AudioFileClip(audio_path)
    total_dur = voice.duration

    # Each beat gets equal duration
    n = max(1, len(bg_paths))
    base_dur = total_dur / n

    print(f"[assemble] Duration: {total_dur:.2f}s, {n} scenes, ~{base_dur:.2f}s each")
    print(f"[assemble] Motion effect: {motion_effect}")

    # Build scenes
    print(f"[assemble] Building {n} scenes…")
    scenes = []
    for i, img_path in enumerate(bg_paths):
        scene = _prepare_image(img_path, base_dur, i, motion_effect)
        scenes.append(scene)

    # Concatenate scenes
    print("[assemble] Concatenating scenes…")
    video = concatenate_videoclips(scenes, method="compose")

    # Sync video length to voice
    if video.duration > total_dur:
        video = video.subclip(0, total_dur)
    else:
        video = video.set_duration(total_dur)

    # Add voice audio
    print("[assemble] Adding narration audio…")
    final_audio = voice.volumex(voice_volume)

    # Add background music
    if os.path.isdir(music_dir):
        music_files = [
            os.path.join(music_dir, f)
            for f in os.listdir(music_dir)
            if f.lower().endswith((".mp3", ".wav", ".m4a"))
        ]
    else:
        music_files = []

    if music_files:
        music_path = random.choice(music_files)
        print(f"[assemble] Adding background music: {music_path}")
        bgm = AudioFileClip(music_path)

        loops = int(total_dur // bgm.duration) + 1
        bgm_full = concatenate_audioclips([bgm] * loops).subclip(0, total_dur)
        bgm_full = bgm_full.volumex(music_volume)

        final_audio = CompositeAudioClip([final_audio, bgm_full])

    video = video.set_audio(final_audio)

    # Write output
    print(f"[assemble] Writing video → {out_path}")
    video.write_videofile(
        out_path,
        fps=DEFAULT_FPS,
        codec="libx264",
        audio_codec="aac",
        bitrate="6M",
        threads=8,
    )
    print(f"[assemble] Done → {out_path}")


def list_motion_effects() -> list[str]:
    """Return list of available motion effects."""
    return list(MOTION_EFFECTS.keys())
