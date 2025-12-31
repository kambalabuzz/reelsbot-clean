# cache_utils.py
"""
Cache management utilities.
View, clear, and manage all cached assets.
"""

from pathlib import Path
import shutil

# All cache directories
CACHE_DIRS = {
    "beats": Path("cache/beats"),
    "audio": Path("cache/audio"),
    "trimmed_audio": Path("cache/trimmed_audio"),
    "alignment": Path("cache/alignment"),
    "images": Path("media_cache"),
}


def get_cache_stats() -> dict:
    """Get stats for all caches."""
    stats = {}
    
    for name, cache_dir in CACHE_DIRS.items():
        if not cache_dir.exists():
            stats[name] = {"files": 0, "size_mb": 0}
            continue
        
        files = list(cache_dir.glob("*"))
        total_size = sum(f.stat().st_size for f in files if f.is_file())
        
        stats[name] = {
            "files": len(files),
            "size_mb": round(total_size / (1024 * 1024), 2),
        }
    
    return stats


def print_cache_stats():
    """Print cache statistics."""
    stats = get_cache_stats()
    
    print("\n" + "="*50)
    print("CACHE STATISTICS")
    print("="*50)
    
    total_files = 0
    total_size = 0
    
    for name, data in stats.items():
        print(f"  {name:20} {data['files']:5} files  {data['size_mb']:8.2f} MB")
        total_files += data['files']
        total_size += data['size_mb']
    
    print("-"*50)
    print(f"  {'TOTAL':20} {total_files:5} files  {total_size:8.2f} MB")
    print("="*50 + "\n")


def clear_cache(cache_name: str = "all"):
    """
    Clear specific cache or all caches.
    
    Args:
        cache_name: Name of cache to clear, or "all" for everything
    """
    if cache_name == "all":
        for name, cache_dir in CACHE_DIRS.items():
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
                print(f"[cache] Cleared {name}")
        print("[cache] All caches cleared")
    elif cache_name in CACHE_DIRS:
        cache_dir = CACHE_DIRS[cache_name]
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
            print(f"[cache] Cleared {cache_name}")
        else:
            print(f"[cache] {cache_name} is already empty")
    else:
        print(f"[cache] Unknown cache: {cache_name}")
        print(f"[cache] Available: {', '.join(CACHE_DIRS.keys())}, all")


def clear_old_cache(days: int = 7):
    """
    Clear cache files older than N days.
    
    Args:
        days: Delete files older than this many days
    """
    import time
    
    cutoff = time.time() - (days * 24 * 60 * 60)
    deleted = 0
    
    for name, cache_dir in CACHE_DIRS.items():
        if not cache_dir.exists():
            continue
        
        for f in cache_dir.glob("*"):
            if f.is_file() and f.stat().st_mtime < cutoff:
                f.unlink()
                deleted += 1
    
    print(f"[cache] Deleted {deleted} files older than {days} days")


def estimate_savings(topic: str) -> dict:
    """
    Estimate API cost savings from cache for a topic.
    
    Returns dict with estimated costs saved.
    """
    from openai_utils import safe_filename, _beats_cache_path
    
    slug = safe_filename(topic)
    savings = {
        "beats": 0,
        "images": 0,
        "audio": 0,
        "total_usd": 0,
    }
    
    # Check if beats are cached
    beats_path = _beats_cache_path(topic, 12, "true_crime")
    if beats_path.exists():
        savings["beats"] = 1
        savings["total_usd"] += 0.01  # ~$0.01 for GPT call
    
    # Check for cached images (rough estimate)
    image_cache = CACHE_DIRS["images"]
    if image_cache.exists():
        cached_images = list(image_cache.glob(f"*{slug}*.png"))
        savings["images"] = len(cached_images)
        savings["total_usd"] += len(cached_images) * 0.04  # ~$0.04 per image
    
    # Check for cached audio
    audio_cache = CACHE_DIRS["audio"]
    if audio_cache.exists():
        # Can't easily match by topic, just report cache exists
        savings["audio"] = len(list(audio_cache.glob("*.mp3")))
    
    return savings


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print_cache_stats()
        print("Usage:")
        print("  python cache_utils.py stats      - Show cache statistics")
        print("  python cache_utils.py clear      - Clear all caches")
        print("  python cache_utils.py clear NAME - Clear specific cache")
        print("  python cache_utils.py old 7      - Clear files older than 7 days")
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "stats":
        print_cache_stats()
    elif cmd == "clear":
        cache_name = sys.argv[2] if len(sys.argv) > 2 else "all"
        clear_cache(cache_name)
        print_cache_stats()
    elif cmd == "old":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        clear_old_cache(days)
        print_cache_stats()
    else:
        print(f"Unknown command: {cmd}")
