# alignment.py
"""
Word-level alignment using Whisper with caching.
Caches alignment results by audio file hash.
"""

import hashlib
import json
from pathlib import Path

from whisper_timestamped import load_model, transcribe

# Cache directory
ALIGNMENT_CACHE_DIR = Path("cache/alignment")

# Lazy load model (expensive to load)
_model = None


def _get_model():
    """Lazy load Whisper model."""
    global _model
    if _model is None:
        print("[alignment] Loading Whisper model: tiny")
        _model = load_model("tiny")
    return _model


def _get_audio_hash(audio_path: str) -> str:
    """Get hash of audio file for cache key."""
    with open(audio_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def _get_cached_path(audio_hash: str) -> Path:
    """Get path to cached alignment file."""
    ALIGNMENT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return ALIGNMENT_CACHE_DIR / f"{audio_hash}.json"


def align_words(
    audio_path: str, 
    out_json: str,
    use_cache: bool = True,
) -> str:
    """
    Run Whisper-timestamped on audio and save word-level timings.
    
    Args:
        audio_path: Path to audio file
        out_json: Output path for JSON
        use_cache: Whether to use cached alignment if available
    
    Returns:
        Path to the output JSON file
    
    Output format:
    [
      { "word": "DURING", "start": 0.45, "end": 0.82 },
      { "word": "THE",    "start": 0.82, "end": 0.95 },
      ...
    ]
    """
    out_path = Path(out_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Check cache first
    if use_cache:
        audio_hash = _get_audio_hash(audio_path)
        cached_path = _get_cached_path(audio_hash)
        
        if cached_path.exists():
            print(f"[alignment] Using cached alignment → {cached_path}")
            # Copy cached file to output path
            cached_data = cached_path.read_text()
            out_path.write_text(cached_data, encoding="utf-8")
            words = json.loads(cached_data)
            print(f"[alignment] Loaded {len(words)} cached words")
            return str(out_path)

    # Run Whisper
    model = _get_model()
    
    print("[alignment] Transcribing and aligning words…")
    result = transcribe(
        model,
        audio_path,
        verbose=False,
    )

    # Extract words
    words_out = []
    for seg in result.get("segments", []):
        for w in seg.get("words", []):
            words_out.append({
                "word": w["text"],
                "start": float(w["start"]),
                "end": float(w["end"]),
            })

    # Save to output
    json_content = json.dumps(words_out, indent=2)
    out_path.write_text(json_content, encoding="utf-8")

    # Also save to cache
    if use_cache:
        audio_hash = _get_audio_hash(audio_path)
        cached_path = _get_cached_path(audio_hash)
        cached_path.write_text(json_content, encoding="utf-8")
        print(f"[alignment] Cached alignment → {cached_path}")

    print(f"[alignment] Wrote {len(words_out)} words → {out_path}")
    return str(out_path)


def clear_cache():
    """Clear the alignment cache."""
    if ALIGNMENT_CACHE_DIR.exists():
        import shutil
        shutil.rmtree(ALIGNMENT_CACHE_DIR)
        print("[alignment] Cache cleared")


def get_cache_size() -> int:
    """Get total size of cached alignments in bytes."""
    if not ALIGNMENT_CACHE_DIR.exists():
        return 0
    return sum(f.stat().st_size for f in ALIGNMENT_CACHE_DIR.glob("*.json"))


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        align_words(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python alignment.py <audio.mp3> <output.json>")
