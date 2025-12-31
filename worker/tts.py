# tts.py
"""
Text-to-Speech using OpenAI TTS or ElevenLabs with caching.
Caches audio by script hash + voice to avoid regenerating.
"""

import hashlib
import os
import subprocess
import tempfile
from pathlib import Path
from openai import OpenAI
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

# Import voice library to detect provider
from voice_library import get_library, VoiceProvider

openai_client = OpenAI()
elevenlabs_client = ElevenLabs(api_key=os.environ.get("ELEVENLABS_API_KEY"))

# Cache directory
AUDIO_CACHE_DIR = Path("cache/audio")


def _get_cache_key(text: str, voice: str, model: str) -> str:
    """Generate cache key from text + voice + model."""
    content = f"{model}:{voice}:{text}"
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def _get_cached_path(cache_key: str) -> Path:
    """Get path to cached audio file."""
    AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return AUDIO_CACHE_DIR / f"{cache_key}.mp3"


def synthesize(
    text: str,
    out_path: str,
    voice: str = "alloy",
    model: str = "gpt-4o-mini-tts",
    use_cache: bool = True,
) -> str:
    """
    Generate narration using OpenAI TTS or ElevenLabs.
    Automatically detects provider from voice_library.

    Args:
        text: The text to speak
        out_path: Where to save the output
        voice: Voice persona ID (e.g., "adam", "emma") or provider voice ID
        model: TTS model (only used for OpenAI)
        use_cache: Whether to use cached audio if available

    Returns:
        Path to the generated audio file
    """
    out_path = str(out_path)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    # Get voice info from library
    lib = get_library()
    voice_persona = lib.get_voice(voice)

    # Determine provider and actual voice ID
    if voice_persona:
        provider = voice_persona.provider
        provider_voice_id = voice_persona.provider_voice_id
        print(f"[tts] Using {provider.value.upper()} voice: {voice_persona.name} ({provider_voice_id})")
    else:
        # Fallback: assume OpenAI if voice not found in library
        provider = VoiceProvider.OPENAI
        provider_voice_id = voice
        print(f"[tts] Voice '{voice}' not in library, assuming OpenAI: {provider_voice_id}")

    # Check cache first
    if use_cache:
        cache_key = _get_cache_key(text, provider_voice_id, str(provider))
        cached_path = _get_cached_path(cache_key)

        if cached_path.exists():
            print(f"[tts] Using cached audio → {cached_path}")
            # Copy cached file to output path
            Path(out_path).write_bytes(cached_path.read_bytes())
            return out_path

    # Generate audio based on provider
    if provider == VoiceProvider.ELEVENLABS:
        audio_bytes = _synthesize_elevenlabs(text, provider_voice_id)
    else:
        audio_bytes = _synthesize_openai(text, provider_voice_id, model)

    # Save to temporary path first
    temp_path = out_path + ".temp.mp3"
    with open(temp_path, "wb") as f:
        f.write(audio_bytes)

    # Trim silence between words (keep silences under 0.5s)
    try:
        _trim_silence(temp_path, out_path)
        os.remove(temp_path)
    except Exception as e:
        print(f"[tts] Warning: silence trimming failed: {e}, using original audio")
        os.rename(temp_path, out_path)

    # Also save to cache
    if use_cache:
        cache_key = _get_cache_key(text, provider_voice_id, str(provider))
        cached_path = _get_cached_path(cache_key)
        cached_path.write_bytes(Path(out_path).read_bytes())
        print(f"[tts] Cached audio → {cached_path}")

    print(f"[tts] Saved narration → {out_path}")
    return out_path


def _synthesize_openai(text: str, voice: str, model: str) -> bytes:
    """Generate audio using OpenAI TTS."""
    print(f"[tts] Generating with OpenAI TTS (voice: {voice}, model: {model})...")

    response = openai_client.audio.speech.create(
        model=model,
        voice=voice,
        input=text
    )

    return response.read()


def _synthesize_elevenlabs(text: str, voice_id: str) -> bytes:
    """Generate audio using ElevenLabs with optimized settings for narrative quality."""
    print(f"[tts] Generating with ElevenLabs (voice_id: {voice_id})...")

    # Generate audio with optimized settings for engaging storytelling
    audio_generator = elevenlabs_client.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        model_id="eleven_turbo_v2_5",  # Fast, high-quality model
        voice_settings=VoiceSettings(
            stability=0.4,  # Lower for more emotion and variation
            similarity_boost=0.85,  # Higher to maintain voice character
            style=0.3,  # Moderate style exaggeration for engaging delivery
            use_speaker_boost=True
        )
    )

    # Collect all audio chunks
    audio_bytes = b"".join(audio_generator)
    return audio_bytes


def _trim_silence(input_path: str, output_path: str, max_silence: float = 0.25):
    """
    Trim long silences between words using FFmpeg silenceremove filter.
    Creates continuous narration by aggressively removing pauses while preserving emotion.
    Keeps silences under max_silence seconds for engaging delivery.
    """
    print(f"[tts] Trimming silence for continuous narration (max: {max_silence}s)...")

    # Use FFmpeg to remove silences longer than max_silence
    # More aggressive trimming for continuous engaging narration
    # Lower threshold (-40dB) to catch softer pauses while keeping emotion
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-af", f"silenceremove=start_periods=1:start_silence=0.05:start_threshold=-40dB,silenceremove=stop_periods=-1:stop_duration={max_silence}:stop_threshold=-40dB",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise Exception(f"FFmpeg failed: {result.stderr[:200]}")

    print(f"[tts] Silence trimmed successfully")


def clear_cache():
    """Clear the audio cache."""
    if AUDIO_CACHE_DIR.exists():
        import shutil
        shutil.rmtree(AUDIO_CACHE_DIR)
        print("[tts] Cache cleared")


def get_cache_size() -> int:
    """Get total size of cached audio in bytes."""
    if not AUDIO_CACHE_DIR.exists():
        return 0
    return sum(f.stat().st_size for f in AUDIO_CACHE_DIR.glob("*.mp3"))


if __name__ == "__main__":
    # Test
    text = "This is a test of the caching system."
    synthesize(text, "test_output.mp3", voice="nova")
    print(f"Cache size: {get_cache_size() / 1024:.1f} KB")
