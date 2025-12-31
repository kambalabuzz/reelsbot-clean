# main.py
import os
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from openai_utils import generate_story_beats, generate_images, safe_filename
from tts import synthesize
from assemble import assemble
from alignment import align_words
from captions import build_ass_from_alignment, burn_captions

load_dotenv()

# Ensure base folders exist
Path("outputs").mkdir(exist_ok=True)
Path("media_cache").mkdir(exist_ok=True)
Path("assets/music").mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    # ------------------ CLI ------------------
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", required=True, help="topic or case name")
    ap.add_argument("--beats", type=int, default=12)
    ap.add_argument("--template", default="./templates/default.json")
    args = ap.parse_args()

    topic = args.topic
    beats_count = args.beats

    # ------------------ RUN FOLDER ------------------
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = safe_filename(topic)

    run_root = Path("outputs") / f"{ts}_{slug}"
    audio_dir = run_root / "audio"
    image_dir = run_root / "images"
    align_dir = run_root / "alignment"
    video_dir = run_root / "video"
    final_dir = run_root / "final"

    for d in [run_root, audio_dir, image_dir, align_dir, video_dir, final_dir]:
        d.mkdir(parents=True, exist_ok=True)

    print(f"[run] Saving everything under: {run_root}\n")

    # ------------------ 1. STORY BEATS ------------------
    print(f"[1/5] Loading or generating beats for topic: {topic!r}")
    beats = generate_story_beats(topic, beats=beats_count)

    lines = [b["line"] for b in beats]
    visuals = [b["visual"] for b in beats]

    script_text = " ".join(lines)
    print(f"Total narration words: {len(script_text.split())}\n")

    # ------------------ 2. VOICEOVER ------------------
    print("[2/5] Generating voiceover with ElevenLabs…")
    voice_path = audio_dir / "voice.mp3"
    synthesize(script_text, str(voice_path))
    print(f"[ok] Voice saved → {voice_path}\n")

    # ------------------ 3. IMAGES (with caching) ------------------
    print(f"[3/5] Generating {len(visuals)} scene images (cached if available)…")

    img_paths = []

    base_style = (
        "cinematic digital comic illustration, creepy but colorful, "
        "muted blues and orange contrast, graphic novel vibe, dramatic lighting, "
        "expressive faces, vertical 9:16 frame, no text, no watermark. "
    )

    for i, visual in enumerate(visuals, start=1):
        prompt = (
            f"{base_style}"
            f"Frame {i} in a dark true-crime short. "
            f"Show this scene: {visual}"
        )

        # 👇 IMPORTANT: give each beat its own cache key
        img = generate_images(
            prompt,
            out_dir="media_cache",
            n=1,
            uniq=f"beat_{i:02d}",
        )[0]

        src = Path(img)
        dst = image_dir / f"beat_{i:02d}{src.suffix}"
        dst.write_bytes(src.read_bytes())
        img_paths.append(str(dst))

        print(f"  [beat {i:02d}] {dst}")

        print("\n[ok] All images ready.\n")

    # ------------------ 4. RAW VIDEO ASSEMBLY ------------------
    print("[4/5] Assembling raw video (no captions)…")
    raw_video = video_dir / "reel_base.mp4"

    assemble(
        script_text=script_text,
        audio_path=str(voice_path),
        bg_paths=img_paths,
        cfg_path=args.template,
        music_dir="assets/music",
        out_path=str(raw_video),
        lines=lines,
    )

    print(f"[ok] Raw video saved → {raw_video}\n")

    # ------------------ 5. CAPTIONS: ALIGN → ASS → BURN ------------------
    print("[5/5] Running Whisper alignment…")
    alignment_json = align_dir / "words.json"

    # align_words only expects: audio_path, out_json
    align_words(str(voice_path), str(alignment_json))

    print(f"[ok] Alignment saved → {alignment_json}")

    # Build ASS file
    ass_path = video_dir / "captions.ass"
    build_ass_from_alignment(str(alignment_json), str(ass_path))
    print(f"[ok] ASS subtitles generated → {ass_path}")

    # Burn final captions
    final_video = final_dir / "reel.mp4"
    burn_captions(str(raw_video), str(ass_path), str(final_video))
    print(f"[ok] Final reel saved → {final_video}\n")

    print("🎉 DONE!")