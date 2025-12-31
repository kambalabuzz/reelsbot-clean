# audio_utils.py
"""
Audio processing utilities with caching.
"""

import hashlib
from pathlib import Path
from pydub import AudioSegment
from pydub.silence import split_on_silence

# Cache directory
TRIMMED_CACHE_DIR = Path("cache/trimmed_audio")


def _get_audio_hash(audio_path: str) -> str:
    """Get hash of audio file for cache key."""
    with open(audio_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def _get_cached_path(audio_hash: str, params_hash: str) -> Path:
    """Get path to cached trimmed audio."""
    TRIMMED_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return TRIMMED_CACHE_DIR / f"{audio_hash}_{params_hash}.mp3"


def trim_silence(
    in_path: str,
    out_path: str,
    min_silence_len: int = 450,
    silence_thresh: float | None = None,
    keep_silence: int = 120,
    use_cache: bool = True,
) -> str:
    """
    Load an audio file, remove long silent gaps, and save to out_path.
    
    Args:
        in_path: Input audio file
        out_path: Output audio file
        min_silence_len: Minimum silence length to trim (ms)
        silence_thresh: Silence threshold in dBFS (None = auto)
        keep_silence: How much silence to keep at cuts (ms)
        use_cache: Whether to use cached trimmed audio
    
    Returns:
        Path to the trimmed audio file
    """
    in_p = Path(in_path)
    out_p = Path(out_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    # Check cache
    if use_cache:
        audio_hash = _get_audio_hash(in_path)
        params_hash = hashlib.md5(
            f"{min_silence_len}:{keep_silence}".encode()
        ).hexdigest()[:8]
        cached_path = _get_cached_path(audio_hash, params_hash)
        
        if cached_path.exists():
            print(f"[audio] Using cached trimmed audio → {cached_path}")
            out_p.write_bytes(cached_path.read_bytes())
            return str(out_p)

    print(f"[audio] Trimming silence from {in_path}…")
    
    audio = AudioSegment.from_file(in_p)
    original_duration = len(audio) / 1000  # seconds

    # Auto silence threshold if not provided
    if silence_thresh is None:
        silence_thresh = audio.dBFS - 12

    # Split on silence
    chunks = split_on_silence(
        audio,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh,
        keep_silence=keep_silence,
    )

    # Edge case: no chunks detected
    if not chunks:
        print("[audio] No silence detected, copying original")
        out_p.write_bytes(in_p.read_bytes())
        return str(out_p)

    # Concatenate chunks
    processed = AudioSegment.empty()
    for ch in chunks:
        processed += ch

    new_duration = len(processed) / 1000
    saved = original_duration - new_duration

    # Export
    ext = out_p.suffix.lstrip(".").lower() or "mp3"
    processed.export(out_p, format=ext)

    print(f"[audio] Trimmed {saved:.1f}s of silence ({original_duration:.1f}s → {new_duration:.1f}s)")

    # Save to cache
    if use_cache:
        audio_hash = _get_audio_hash(in_path)
        params_hash = hashlib.md5(
            f"{min_silence_len}:{keep_silence}".encode()
        ).hexdigest()[:8]
        cached_path = _get_cached_path(audio_hash, params_hash)
        cached_path.write_bytes(out_p.read_bytes())
        print(f"[audio] Cached trimmed audio → {cached_path}")

    return str(out_p)


def get_audio_duration(audio_path: str) -> float:
    """Get duration of audio file in seconds."""
    audio = AudioSegment.from_file(audio_path)
    return len(audio) / 1000


def clear_cache():
    """Clear the trimmed audio cache."""
    if TRIMMED_CACHE_DIR.exists():
        import shutil
        shutil.rmtree(TRIMMED_CACHE_DIR)
        print("[audio] Cache cleared")


def get_cache_size() -> int:
    """Get total size of cached audio in bytes."""
    if not TRIMMED_CACHE_DIR.exists():
        return 0
    return sum(f.stat().st_size for f in TRIMMED_CACHE_DIR.glob("*.mp3"))
