# voice_library.py
"""
Voice library with named personas and multi-language support.
Similar to FacelessReels' voice selection but more flexible.
"""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class VoiceProvider(str, Enum):
    """TTS providers"""
    OPENAI = "openai"
    ELEVENLABS = "elevenlabs"  # Future support


class VoiceGender(str, Enum):
    """Voice gender"""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


class VoiceStyle(str, Enum):
    """Voice style/tone"""
    NARRATOR = "narrator"       # Storytelling
    DRAMATIC = "dramatic"       # Intense, emotional
    CALM = "calm"              # Soothing
    ENERGETIC = "energetic"    # Upbeat
    SERIOUS = "serious"        # Professional
    FRIENDLY = "friendly"      # Warm, approachable
    MYSTERIOUS = "mysterious"  # Eerie, suspenseful


@dataclass
class VoicePersona:
    """A named voice with personality"""
    id: str
    name: str
    description: str
    gender: VoiceGender
    style: VoiceStyle
    provider: VoiceProvider
    provider_voice_id: str  # The actual voice ID for the API
    sample_text: str = "The secrets of the past refuse to stay buried."
    languages: List[str] = None  # Supported language codes
    
    def __post_init__(self):
        if self.languages is None:
            self.languages = ["en"]


# =============================================================================
# ELEVENLABS VOICES WITH PERSONAS (UPDATED IDs)
# =============================================================================

ELEVENLABS_VOICES = [
    # Female voices
    VoicePersona(
        id="emma",
        name="Emma",
        description="Soft and soothing. Perfect for calm, relaxing content.",
        gender=VoiceGender.FEMALE,
        style=VoiceStyle.CALM,
        provider=VoiceProvider.ELEVENLABS,
        provider_voice_id="56bWURjYFHyYyVf490Dp",  # Emma's ElevenLabs ID
        languages=["en"],
    ),
    VoicePersona(
        id="sarah",
        name="Sarah",
        description="Warm and engaging. Great for lifestyle and motivation.",
        gender=VoiceGender.FEMALE,
        style=VoiceStyle.FRIENDLY,
        provider=VoiceProvider.ELEVENLABS,
        provider_voice_id="EXAVITQu4vr4xnSDxMaL",  # Sarah's ElevenLabs ID
        languages=["en"],
    ),

    # Male voices
    VoicePersona(
        id="alex",
        name="Alex",
        description="Neutral and versatile. Works for any content type.",
        gender=VoiceGender.NEUTRAL,
        style=VoiceStyle.FRIENDLY,
        provider=VoiceProvider.ELEVENLABS,
        provider_voice_id="uf0ZrRtyyJlbbGIn43uD",  # Alex's ElevenLabs ID
        languages=["en"],
    ),
    VoicePersona(
        id="adam",
        name="Adam",
        description="The well-known voice of TikTok and Instagram. Deep and authoritative.",
        gender=VoiceGender.MALE,
        style=VoiceStyle.NARRATOR,
        provider=VoiceProvider.ELEVENLABS,
        provider_voice_id="pNInz6obpgDQGcFmaJgB",  # Adam's ElevenLabs ID
        languages=["en"],
    ),
    VoicePersona(
        id="john",
        name="John",
        description="The perfect storyteller. Very realistic and natural.",
        gender=VoiceGender.MALE,
        style=VoiceStyle.DRAMATIC,
        provider=VoiceProvider.ELEVENLABS,
        provider_voice_id="xUwWtrwxKYQAFNPrH25f",  # John's ElevenLabs ID
        languages=["en"],
    ),
]

# Fallback to OpenAI voices if needed
OPENAI_VOICES = [
    VoicePersona(
        id="adam_openai",
        name="Adam (OpenAI)",
        description="Fallback: Deep and authoritative OpenAI voice.",
        gender=VoiceGender.MALE,
        style=VoiceStyle.NARRATOR,
        provider=VoiceProvider.OPENAI,
        provider_voice_id="onyx",
        languages=["en", "es", "fr", "de", "it", "pt", "pl", "ru", "ja", "ko", "zh"],
    ),
]


# =============================================================================
# LANGUAGE SUPPORT
# =============================================================================

SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "flag": "🇺🇸", "native": "English"},
    "es": {"name": "Spanish", "flag": "🇪🇸", "native": "Español"},
    "fr": {"name": "French", "flag": "🇫🇷", "native": "Français"},
    "de": {"name": "German", "flag": "🇩🇪", "native": "Deutsch"},
    "it": {"name": "Italian", "flag": "🇮🇹", "native": "Italiano"},
    "pt": {"name": "Portuguese", "flag": "🇧🇷", "native": "Português"},
    "nl": {"name": "Dutch", "flag": "🇳🇱", "native": "Nederlands"},
    "pl": {"name": "Polish", "flag": "🇵🇱", "native": "Polski"},
    "ru": {"name": "Russian", "flag": "🇷🇺", "native": "Русский"},
    "ja": {"name": "Japanese", "flag": "🇯🇵", "native": "日本語"},
    "ko": {"name": "Korean", "flag": "🇰🇷", "native": "한국어"},
    "zh": {"name": "Chinese", "flag": "🇨🇳", "native": "中文"},
    "ar": {"name": "Arabic", "flag": "🇸🇦", "native": "العربية"},
    "hi": {"name": "Hindi", "flag": "🇮🇳", "native": "हिन्दी"},
    "tr": {"name": "Turkish", "flag": "🇹🇷", "native": "Türkçe"},
    "sv": {"name": "Swedish", "flag": "🇸🇪", "native": "Svenska"},
    "no": {"name": "Norwegian", "flag": "🇳🇴", "native": "Norsk"},
    "da": {"name": "Danish", "flag": "🇩🇰", "native": "Dansk"},
    "fi": {"name": "Finnish", "flag": "🇫🇮", "native": "Suomi"},
    "id": {"name": "Indonesian", "flag": "🇮🇩", "native": "Bahasa Indonesia"},
    "th": {"name": "Thai", "flag": "🇹🇭", "native": "ไทย"},
    "vi": {"name": "Vietnamese", "flag": "🇻🇳", "native": "Tiếng Việt"},
}


# =============================================================================
# VOICE LIBRARY CLASS
# =============================================================================

class VoiceLibrary:
    """Manages voice personas and language support"""

    def __init__(self):
        # Prioritize ElevenLabs voices, fallback to OpenAI
        self._voices = {v.id: v for v in ELEVENLABS_VOICES + OPENAI_VOICES}
    
    def get_voice(self, voice_id: str) -> Optional[VoicePersona]:
        """Get a voice by ID"""
        return self._voices.get(voice_id)
    
    def get_provider_voice_id(self, voice_id: str) -> str:
        """Get the actual provider voice ID (e.g., 'onyx' for OpenAI)"""
        voice = self.get_voice(voice_id)
        if voice:
            return voice.provider_voice_id
        # Fallback: assume it's already a provider voice ID
        return voice_id
    
    def get_all_voices(self) -> List[VoicePersona]:
        """Get all available voices"""
        return list(self._voices.values())
    
    def get_voices_by_gender(self, gender: VoiceGender) -> List[VoicePersona]:
        """Get voices filtered by gender"""
        return [v for v in self._voices.values() if v.gender == gender]
    
    def get_voices_by_style(self, style: VoiceStyle) -> List[VoicePersona]:
        """Get voices filtered by style"""
        return [v for v in self._voices.values() if v.style == style]
    
    def get_voices_for_language(self, language_code: str) -> List[VoicePersona]:
        """Get voices that support a specific language"""
        return [v for v in self._voices.values() if language_code in v.languages]
    
    def get_recommended_voice(self, niche: str, gender: Optional[VoiceGender] = None) -> VoicePersona:
        """Get recommended voice for a content niche"""
        
        # Niche to style mapping
        niche_styles = {
            "true_crime": VoiceStyle.MYSTERIOUS,
            "horror": VoiceStyle.MYSTERIOUS,
            "mystery": VoiceStyle.DRAMATIC,
            "history": VoiceStyle.NARRATOR,
            "conspiracy": VoiceStyle.DRAMATIC,
            "paranormal": VoiceStyle.MYSTERIOUS,
            "sci_fi": VoiceStyle.NARRATOR,
            "motivation": VoiceStyle.ENERGETIC,
            "finance": VoiceStyle.SERIOUS,
            "tech": VoiceStyle.FRIENDLY,
        }
        
        target_style = niche_styles.get(niche, VoiceStyle.NARRATOR)
        
        # Find matching voices
        matches = self.get_voices_by_style(target_style)
        
        # Filter by gender if specified
        if gender and matches:
            gender_matches = [v for v in matches if v.gender == gender]
            if gender_matches:
                matches = gender_matches
        
        # Return first match or default
        if matches:
            return matches[0]
        
        return self._voices.get("adam", OPENAI_VOICES[0])
    
    def list_languages(self) -> List[dict]:
        """Get list of supported languages"""
        return [
            {"code": code, **info}
            for code, info in SUPPORTED_LANGUAGES.items()
        ]
    
    def get_language_info(self, code: str) -> Optional[dict]:
        """Get info about a specific language"""
        if code in SUPPORTED_LANGUAGES:
            return {"code": code, **SUPPORTED_LANGUAGES[code]}
        return None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

_library = None

def get_library() -> VoiceLibrary:
    """Get the global voice library instance"""
    global _library
    if _library is None:
        _library = VoiceLibrary()
    return _library


def get_voice_for_tts(voice_id: str) -> str:
    """
    Convert a persona voice ID to the actual TTS provider voice ID.
    Use this when calling the TTS API.
    """
    lib = get_library()
    return lib.get_provider_voice_id(voice_id)


if __name__ == "__main__":
    lib = get_library()
    
    print("=== AVAILABLE VOICES ===")
    for voice in lib.get_all_voices():
        print(f"\n  {voice.name} ({voice.id})")
        print(f"    Gender: {voice.gender.value}")
        print(f"    Style: {voice.style.value}")
        print(f"    {voice.description}")
        print(f"    Languages: {', '.join(voice.languages)}")
    
    print("\n=== VOICES FOR TRUE CRIME ===")
    rec = lib.get_recommended_voice("true_crime")
    print(f"  Recommended: {rec.name} - {rec.description}")
    
    print("\n=== SUPPORTED LANGUAGES ===")
    for lang in lib.list_languages()[:10]:
        print(f"  {lang['flag']} {lang['name']} ({lang['native']})")
    print(f"  ... and {len(lib.list_languages()) - 10} more")
