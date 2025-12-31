# engine.py
"""
Main video generation engine.
Now accepts SeriesConfig/EpisodeConfig for full customization.
"""

from pathlib import Path
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv

from config import (
    SeriesConfig, EpisodeConfig, CaptionStyle, VoiceOption, 
    ArtStyle, MotionEffect, Niche, ART_STYLE_PROMPTS
)
from openai_utils import generate_story_beats, generate_images, safe_filename
from tts import synthesize
from assemble import assemble
from alignment import align_words
from captions import build_ass_from_alignment, burn_captions, list_styles
from audio_utils import trim_silence
from voice_library import get_library as get_voice_library, get_voice_for_tts
from music_library import get_library as get_music_library

load_dotenv()


def generate_episode(
    # Required
    topic: str,
    
    # NEW: Full config objects (preferred)
    series_config: Optional[SeriesConfig] = None,
    episode_config: Optional[EpisodeConfig] = None,
    
    # Legacy params (used if no config provided)
    beats_count: int = 12,
    music_dir: str = "assets/music",
    template_path: str = "./templates/default.json",
    outputs_root: str = "outputs",
    
    # NEW: Direct style overrides (for quick testing)
    caption_style: str = "red_highlight",
    voice: str = "alloy",
    art_style: str = "comic_dark",
    niche: str = "true_crime",
    motion_effect: str = "ken_burns",
    
    # NEW: Watermark control
    add_watermark: bool = False,
) -> dict:
    """
    Generate a complete video episode.
    
    Can be called three ways:
    1. With EpisodeConfig (full control, preferred for SaaS)
    2. With SeriesConfig + topic (uses series defaults)
    3. With individual params (legacy/testing)
    
    Returns dict with paths to all generated assets.
    """
    
    # Resolve config
    if episode_config:
        # Full episode config provided
        topic = episode_config.topic
        caption_style = episode_config.caption_style.value
        voice = episode_config.voice.value
        art_style = episode_config.art_style.value
        niche = episode_config.series_config.niche.value
        motion_effect = episode_config.series_config.motion_effect.value
        beats_count = episode_config.series_config.beats_per_episode
        add_watermark = episode_config.series_config.add_watermark
        music_dir = episode_config.series_config.music_track or music_dir
        
    elif series_config:
        # Series config provided, use its defaults
        caption_style = series_config.caption_style.value
        voice = series_config.voice.value
        art_style = series_config.art_style.value
        niche = series_config.niche.value
        motion_effect = series_config.motion_effect.value
        beats_count = series_config.beats_per_episode
        add_watermark = series_config.add_watermark
        if series_config.music_track:
            music_dir = series_config.music_track
    
    # Validate caption style
    available_styles = list_styles()
    if caption_style not in available_styles:
        print(f"[engine] Unknown caption style '{caption_style}', using 'red_highlight'")
        caption_style = "red_highlight"
    
    # Get art style prompt
    try:
        art_style_enum = ArtStyle(art_style)
        art_prompt_base = ART_STYLE_PROMPTS.get(art_style_enum, ART_STYLE_PROMPTS[ArtStyle.COMIC_DARK])
    except ValueError:
        art_prompt_base = ART_STYLE_PROMPTS[ArtStyle.COMIC_DARK]
    
    # ------------------ RUN FOLDER ------------------
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = safe_filename(topic)
    run_root = Path(outputs_root) / f"{ts}_{slug}"

    audio_dir = run_root / "audio"
    image_dir = run_root / "images"
    align_dir = run_root / "alignment"
    video_dir = run_root / "video"
    final_dir = run_root / "final"

    for d in [run_root, audio_dir, image_dir, align_dir, video_dir, final_dir]:
        d.mkdir(parents=True, exist_ok=True)

    print(f"[engine] Run folder → {run_root}")
    print(f"[engine] Settings: caption={caption_style}, voice={voice}, art={art_style}, niche={niche}")

    # ------------------ STORY BEATS ------------------
    print(f"[engine] Generating {beats_count} beats for topic: {topic!r}")
    beats = generate_story_beats(topic, beats=beats_count, niche=niche)
    lines = [b["line"] for b in beats]
    visuals = [b["visual"] for b in beats]
    script_text = " ".join(lines)
    print(f"[engine] Narration words: {len(script_text.split())}")

    # ------------------ VOICEOVER ------------------
    raw_voice_path = audio_dir / "voice_raw.mp3"
    final_voice_path = audio_dir / "voice.mp3"

    # Convert voice persona ID to actual TTS voice ID
    tts_voice = get_voice_for_tts(voice)
    print(f"[engine] Generating narration with voice: {voice} (TTS: {tts_voice})")
    synthesize(script_text, str(raw_voice_path), voice=tts_voice)

    print("[engine] Trimming silence…")
    trim_silence(
        str(raw_voice_path),
        str(final_voice_path),
        min_silence_len=450,
        keep_silence=130
    )

    voice_path = final_voice_path
    print(f"[engine] Voice saved → {voice_path}")

    # ------------------ IMAGES ------------------
    print(f"[engine] Generating {len(visuals)} images with style: {art_style}")
    img_paths = []

    media_cache = Path("media_cache")
    media_cache.mkdir(exist_ok=True)

    for i, visual in enumerate(visuals, start=1):
        prompt = (
            f"{art_prompt_base}. "
            f"Frame {i} in a {niche.replace('_', ' ')} short video. "
            f"Scene: {visual}"
        )

        img = generate_images(
            prompt, 
            out_dir=str(media_cache), 
            n=1,
            uniq=f"{slug}_beat_{i:02d}"
        )[0]
        
        src = Path(img)
        dst = image_dir / f"beat_{i:02d}{src.suffix}"
        dst.write_bytes(src.read_bytes())
        img_paths.append(str(dst))
        print(f"  [beat {i:02d}] {dst}")

    # ------------------ ASSEMBLE RAW VIDEO ------------------
    raw_video = video_dir / "reel_base.mp4"

    print(f"[engine] Assembling video with motion: {motion_effect}")
    assemble(
        script_text=script_text,
        audio_path=str(voice_path),
        bg_paths=img_paths,
        cfg_path=template_path,
        music_dir=music_dir,
        out_path=str(raw_video),
        lines=lines,
        motion_effect=motion_effect,
    )
    print(f"[engine] Raw video → {raw_video}")

    # ------------------ WORD ALIGNMENT ------------------
    alignment_json = align_dir / "words.json"
    print("[engine] Running Whisper alignment…")
    align_words(str(voice_path), str(alignment_json))
    print(f"[engine] Alignment JSON → {alignment_json}")

    # ------------------ BUILD ASS CAPTIONS ------------------
    ass_path = video_dir / "captions.ass"
    print(f"[engine] Building captions with style: {caption_style}")
    build_ass_from_alignment(
        str(alignment_json), 
        str(ass_path),
        style=caption_style
    )
    print(f"[engine] ASS → {ass_path}")

    # ------------------ BURN FINAL VIDEO ------------------
    final_video = final_dir / "reel.mp4"
    burn_captions(str(raw_video), str(ass_path), str(final_video))
    print(f"[engine] Final reel → {final_video}")

    # ------------------ WATERMARK (if required) ------------------
    if add_watermark:
        print("[engine] Adding watermark…")
        watermarked_video = final_dir / "reel_watermarked.mp4"
        add_watermark_to_video(str(final_video), str(watermarked_video))
        final_video = watermarked_video

    return {
        "run_root": str(run_root),
        "raw_video": str(raw_video),
        "final_video": str(final_video),
        "audio_path": str(voice_path),
        "image_paths": img_paths,
        "alignment_json": str(alignment_json),
        "ass_path": str(ass_path),
        "config": {
            "topic": topic,
            "caption_style": caption_style,
            "voice": voice,
            "art_style": art_style,
            "niche": niche,
            "motion_effect": motion_effect,
            "beats_count": beats_count,
        }
    }


def add_watermark_to_video(input_path: str, output_path: str):
    """Add watermark overlay to video (for free tier)."""
    import subprocess
    
    # Simple text watermark using ffmpeg
    watermark_text = "Made with ReelsBot"
    
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", f"drawtext=text='{watermark_text}':fontsize=24:fontcolor=white@0.5:x=20:y=h-40",
        "-c:a", "copy",
        output_path
    ]
    
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"[engine] Watermarked video → {output_path}")


# =============================================================================
# CLI for testing
# =============================================================================
if __name__ == "__main__":
    import argparse
    
    # Get available voices from voice library
    voice_lib = get_voice_library()
    available_voices = [v.id for v in voice_lib.get_all_voices()]
    # Also allow raw OpenAI voice IDs for backwards compatibility
    available_voices += ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    available_voices = list(set(available_voices))  # Remove duplicates
    
    parser = argparse.ArgumentParser(description="Generate a video episode")
    parser.add_argument("--topic", required=True, help="Episode topic")
    parser.add_argument("--caption-style", default="red_highlight", 
                        choices=list_styles(),
                        help="Caption style")
    parser.add_argument("--voice", default="adam",
                        choices=available_voices,
                        help="Voice persona (adam, john, sarah, etc.) or raw voice ID")
    parser.add_argument("--art-style", default="comic_dark",
                        help="Art style preset")
    parser.add_argument("--niche", default="true_crime",
                        help="Content niche")
    parser.add_argument("--beats", type=int, default=12,
                        help="Number of beats/scenes")
    parser.add_argument("--watermark", action="store_true",
                        help="Add watermark")
    parser.add_argument("--list-voices", action="store_true",
                        help="List available voices and exit")
    
    args = parser.parse_args()
    
    # Handle --list-voices
    if args.list_voices:
        print("\n=== AVAILABLE VOICES ===\n")
        for voice in voice_lib.get_all_voices():
            print(f"  {voice.id:10} - {voice.name} ({voice.gender.value})")
            print(f"             {voice.description}\n")
        exit(0)
    
    result = generate_episode(
        topic=args.topic,
        caption_style=args.caption_style,
        voice=args.voice,
        art_style=args.art_style,
        niche=args.niche,
        beats_count=args.beats,
        add_watermark=args.watermark,
    )
    
    print("\n" + "="*50)
    print("Episode generated successfully!")
    print("="*50)
    for k, v in result.items():
        if k != "config":
            print(f"  {k}: {v}")
    print("\nConfig used:")
    for k, v in result["config"].items():
        print(f"  {k}: {v}")