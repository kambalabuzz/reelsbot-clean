# config.py
"""
Central configuration for all customizable options.
This defines all the "knobs" users can turn when creating a series.
"""

from dataclasses import dataclass, field
from typing import Optional, Literal
from enum import Enum


# =============================================================================
# ENUMS FOR ALL SELECTABLE OPTIONS
# =============================================================================

class CaptionStyle(str, Enum):
    """Available caption styles - matches captions.py STYLES dict"""
    RED_HIGHLIGHT = "red_highlight"
    KARAOKE = "karaoke"
    BEAST = "beast"
    MAJESTIC = "majestic"
    BOLD_STROKE = "bold_stroke"
    SLEEK = "sleek"
    ELEGANT = "elegant"
    NEON = "neon"
    FIRE = "fire"
    HORMOZI = "hormozi"


class Language(str, Enum):
    """Supported languages for TTS and content"""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    DUTCH = "nl"
    POLISH = "pl"
    RUSSIAN = "ru"
    JAPANESE = "ja"
    KOREAN = "ko"
    CHINESE = "zh"
    ARABIC = "ar"
    HINDI = "hi"
    TURKISH = "tr"
    SWEDISH = "sv"
    NORWEGIAN = "no"
    DANISH = "da"
    FINNISH = "fi"
    INDONESIAN = "id"


class VideoDuration(str, Enum):
    """Target video duration options"""
    SHORT = "short"          # 15-30 seconds (6-8 beats)
    MEDIUM = "medium"        # 30-45 seconds (10-12 beats)
    LONG = "long"            # 45-60 seconds (14-16 beats)
    EXTRA_LONG = "extra_long"  # 60-90 seconds (18-20 beats)


DURATION_BEATS = {
    VideoDuration.SHORT: 7,
    VideoDuration.MEDIUM: 11,
    VideoDuration.LONG: 15,
    VideoDuration.EXTRA_LONG: 19,
}


class MusicMood(str, Enum):
    """Background music mood categories"""
    HAPPY = "happy"
    DARK = "dark"
    SUSPENSE = "suspense"
    EPIC = "epic"
    CALM = "calm"
    ENERGETIC = "energetic"
    SAD = "sad"
    MYSTERIOUS = "mysterious"
    UPLIFTING = "uplifting"
    DRAMATIC = "dramatic"


# Language display names
LANGUAGE_NAMES = {
    Language.ENGLISH: "🇺🇸 English",
    Language.SPANISH: "🇪🇸 Spanish",
    Language.FRENCH: "🇫🇷 French",
    Language.GERMAN: "🇩🇪 German",
    Language.ITALIAN: "🇮🇹 Italian",
    Language.PORTUGUESE: "🇧🇷 Portuguese",
    Language.DUTCH: "🇳🇱 Dutch",
    Language.POLISH: "🇵🇱 Polish",
    Language.RUSSIAN: "🇷🇺 Russian",
    Language.JAPANESE: "🇯🇵 Japanese",
    Language.KOREAN: "🇰🇷 Korean",
    Language.CHINESE: "🇨🇳 Chinese",
    Language.ARABIC: "🇸🇦 Arabic",
    Language.HINDI: "🇮🇳 Hindi",
    Language.TURKISH: "🇹🇷 Turkish",
    Language.SWEDISH: "🇸🇪 Swedish",
    Language.NORWEGIAN: "🇳🇴 Norwegian",
    Language.DANISH: "🇩🇰 Danish",
    Language.FINNISH: "🇫🇮 Finnish",
    Language.INDONESIAN: "🇮🇩 Indonesian",
}


class VoiceOption(str, Enum):
    """Available TTS voices"""
    # OpenAI voices
    ALLOY = "alloy"
    ECHO = "echo"
    FABLE = "fable"
    ONYX = "onyx"
    NOVA = "nova"
    SHIMMER = "shimmer"


class ArtStyle(str, Enum):
    """Art style presets for image generation"""
    # Comic styles
    COMIC = "comic"
    COMIC_DARK = "comic_dark"
    CREEPY_COMIC = "creepy_comic"
    
    # Artistic styles
    PAINTING = "painting"
    OIL_PAINTING = "oil_painting"
    WATERCOLOR = "watercolor"
    SKETCH = "sketch"
    
    # Animation styles
    GHIBLI = "ghibli"
    ANIME = "anime"
    DISNEY = "disney"
    PIXAR = "pixar"
    
    # Fantasy/Genre
    DARK_FANTASY = "dark_fantasy"
    CYBERPUNK = "cyberpunk"
    NOIR = "noir"
    STEAMPUNK = "steampunk"
    
    # Fun/Unique
    LEGO = "lego"
    CLAYMATION = "claymation"
    PIXEL_ART = "pixel_art"
    RETRO_90S = "retro_90s"
    
    # Photo styles
    POLAROID = "polaroid"
    REALISTIC = "realistic"
    CINEMATIC = "cinematic"
    FANTASTIC = "fantastic"
    
    # Aesthetic styles
    VAPORWAVE = "vaporwave"
    LOFI = "lofi"
    MINIMALIST = "minimalist"


class Niche(str, Enum):
    """Content niche presets"""
    TRUE_CRIME = "true_crime"
    HORROR = "horror"
    MYSTERY = "mystery"
    HISTORY = "history"
    CONSPIRACY = "conspiracy"
    PARANORMAL = "paranormal"
    SCI_FI = "sci_fi"
    MOTIVATION = "motivation"
    FINANCE = "finance"
    TECH = "tech"


class MotionEffect(str, Enum):
    """Video motion effects"""
    KEN_BURNS = "ken_burns"         # Slow zoom/pan (current default)
    STATIC = "static"               # No movement
    PARALLAX = "parallax"           # Layered depth effect
    SHAKE = "shake"                 # Subtle shake/handheld
    ZOOM_PULSE = "zoom_pulse"       # Rhythmic zoom to beat


class PostFrequency(str, Enum):
    """Auto-posting schedule"""
    MANUAL = "manual"               # No auto-post
    DAILY = "daily"                 # Once per day
    TWICE_DAILY = "twice_daily"     # 2x per day
    THREE_PER_WEEK = "three_per_week"
    WEEKLY = "weekly"


# =============================================================================
# ART STYLE PROMPTS
# =============================================================================

ART_STYLE_PROMPTS = {
    # Comic styles
    ArtStyle.COMIC: (
        "vibrant comic book illustration, bold colors, clean lines, "
        "dynamic composition, professional comic art style, vertical 9:16 frame, "
        "no text, no watermark, no speech bubbles"
    ),
    ArtStyle.COMIC_DARK: (
        "cinematic digital comic illustration, creepy but colorful, "
        "muted blues and orange contrast, graphic novel vibe, dramatic lighting, "
        "expressive faces, vertical 9:16 frame, no text, no watermark"
    ),
    ArtStyle.CREEPY_COMIC: (
        "horror comic book style, unsettling atmosphere, muted desaturated colors, "
        "heavy shadows, suspenseful mood, slightly exaggerated expressions, "
        "vintage horror comic aesthetic, vertical 9:16 frame, no text, no watermark"
    ),
    
    # Artistic styles
    ArtStyle.PAINTING: (
        "classical oil painting style, rich textures, masterful brushstrokes, "
        "Renaissance influence, dramatic chiaroscuro lighting, museum quality art, "
        "vertical 9:16 frame, no text, no watermark"
    ),
    ArtStyle.OIL_PAINTING: (
        "detailed oil painting, thick impasto brushwork, rich deep colors, "
        "classical portrait style, gallery quality fine art, "
        "vertical 9:16 frame, no text, no watermark"
    ),
    ArtStyle.WATERCOLOR: (
        "beautiful watercolor painting, soft edges, flowing transparent colors, "
        "artistic wet-on-wet technique, dreamy ethereal atmosphere, "
        "vertical 9:16 frame, no text, no watermark"
    ),
    ArtStyle.SKETCH: (
        "detailed pencil sketch, professional concept art, crosshatching shading, "
        "artistic linework, dramatic shadows, architectural precision, "
        "vertical 9:16 frame, no text, no watermark"
    ),
    
    # Animation styles
    ArtStyle.GHIBLI: (
        "Studio Ghibli anime style, soft pastel colors, whimsical atmosphere, "
        "detailed backgrounds, magical realism, Hayao Miyazaki inspired, "
        "warm nostalgic feeling, vertical 9:16 frame, no text, no watermark"
    ),
    ArtStyle.ANIME: (
        "modern anime illustration, vibrant colors, detailed character design, "
        "dynamic pose, expressive eyes, professional anime art style, "
        "vertical 9:16 frame, no text, no watermark"
    ),
    ArtStyle.DISNEY: (
        "Disney 3D animation style, Pixar-like rendering, warm expressive characters, "
        "soft lighting, family-friendly aesthetic, big expressive eyes, "
        "polished CGI look, vertical 9:16 frame, no text, no watermark"
    ),
    ArtStyle.PIXAR: (
        "Pixar 3D animation style, highly detailed CGI, expressive characters, "
        "cinematic lighting, emotional storytelling through visuals, "
        "professional animation studio quality, vertical 9:16 frame, no text, no watermark"
    ),
    
    # Fantasy/Genre
    ArtStyle.DARK_FANTASY: (
        "dark fantasy art, gothic atmosphere, dramatic red and black palette, "
        "ominous castles, mystical creatures, epic scale, foreboding mood, "
        "vertical 9:16 frame, no text, no watermark"
    ),
    ArtStyle.CYBERPUNK: (
        "cyberpunk aesthetic, neon lights reflecting on rain-slicked streets, "
        "futuristic noir, holographic advertisements, high-tech low-life, "
        "blade runner inspired, vertical 9:16 frame, no text, no watermark"
    ),
    ArtStyle.NOIR: (
        "film noir style, high contrast black and white with subtle color accents, "
        "dramatic venetian blind shadows, 1940s detective aesthetic, moody atmosphere, "
        "vertical 9:16 frame, no text, no watermark"
    ),
    ArtStyle.STEAMPUNK: (
        "steampunk aesthetic, Victorian era with brass machinery, clockwork gears, "
        "steam-powered technology, copper and bronze tones, industrial fantasy, "
        "vertical 9:16 frame, no text, no watermark"
    ),
    
    # Fun/Unique
    ArtStyle.LEGO: (
        "LEGO minifigure style, plastic toy aesthetic, blocky characters, "
        "bright primary colors, playful scene made of LEGO bricks, "
        "toy photography style, vertical 9:16 frame, no text, no watermark"
    ),
    ArtStyle.CLAYMATION: (
        "claymation stop-motion style, sculpted clay characters, "
        "visible fingerprint textures, Aardman animations inspired, "
        "warm handmade aesthetic, vertical 9:16 frame, no text, no watermark"
    ),
    ArtStyle.PIXEL_ART: (
        "detailed pixel art, 16-bit video game aesthetic, limited color palette, "
        "crisp clean pixels, retro gaming nostalgia, SNES era style, "
        "vertical 9:16 frame, no text, no watermark"
    ),
    ArtStyle.RETRO_90S: (
        "1990s retro aesthetic, VHS tape quality, nostalgic colors, "
        "90s fashion and style, vintage filter, analog warmth, "
        "vertical 9:16 frame, no text, no watermark"
    ),
    
    # Photo styles
    ArtStyle.POLAROID: (
        "polaroid photograph aesthetic, slightly washed out colors, "
        "intimate candid moment, soft vintage filter, authentic film grain, "
        "nostalgic instant camera look, vertical 9:16 frame, no text, no watermark"
    ),
    ArtStyle.REALISTIC: (
        "photorealistic digital art, hyperrealistic details, "
        "cinematic movie still quality, professional photography lighting, "
        "8K ultra HD clarity, vertical 9:16 frame, no text, no watermark"
    ),
    ArtStyle.CINEMATIC: (
        "cinematic movie still, dramatic film lighting, anamorphic lens feel, "
        "Hollywood blockbuster quality, professional color grading, "
        "vertical 9:16 frame, no text, no watermark"
    ),
    ArtStyle.FANTASTIC: (
        "fantasy realism, magical underwater or ethereal environment, "
        "mystical light rays, surreal dreamlike atmosphere, impossible beauty, "
        "vertical 9:16 frame, no text, no watermark"
    ),
    
    # Aesthetic styles
    ArtStyle.VAPORWAVE: (
        "vaporwave aesthetic, pink and cyan neon colors, retro 80s elements, "
        "Greek statues, palm trees, sunset gradients, nostalgic digital art, "
        "vertical 9:16 frame, no text, no watermark"
    ),
    ArtStyle.LOFI: (
        "lofi aesthetic, cozy atmosphere, warm muted colors, "
        "relaxing scene, soft lighting through window, peaceful mood, "
        "vertical 9:16 frame, no text, no watermark"
    ),
    ArtStyle.MINIMALIST: (
        "minimalist illustration, clean simple shapes, limited color palette, "
        "lots of white space, modern graphic design, elegant simplicity, "
        "vertical 9:16 frame, no text, no watermark"
    ),
}


# =============================================================================
# NICHE PROMPTS (for story generation)
# =============================================================================

NICHE_PROMPTS = {
    Niche.TRUE_CRIME: (
        "You are writing a short, fast-paced true crime narration "
        "for a 45-60 second vertical video. Focus on unsolved cases, "
        "mysterious disappearances, or chilling criminal cases."
    ),
    Niche.HORROR: (
        "You are writing a short, spine-chilling horror narration "
        "for a 45-60 second vertical video. Focus on creepy encounters, "
        "unexplained phenomena, or terrifying true stories."
    ),
    Niche.MYSTERY: (
        "You are writing a short, intriguing mystery narration "
        "for a 45-60 second vertical video. Focus on unsolved puzzles, "
        "strange occurrences, or baffling historical mysteries."
    ),
    Niche.HISTORY: (
        "You are writing a short, engaging historical narration "
        "for a 45-60 second vertical video. Focus on fascinating "
        "historical events, forgotten stories, or surprising facts."
    ),
    Niche.CONSPIRACY: (
        "You are writing a short, thought-provoking narration about "
        "conspiracy theories for a 45-60 second vertical video. "
        "Present theories objectively and let viewers decide."
    ),
    Niche.PARANORMAL: (
        "You are writing a short, eerie paranormal narration "
        "for a 45-60 second vertical video. Focus on ghost sightings, "
        "UFO encounters, or unexplained supernatural events."
    ),
    Niche.SCI_FI: (
        "You are writing a short, mind-bending sci-fi narration "
        "for a 45-60 second vertical video. Focus on futuristic concepts, "
        "space mysteries, or technological what-ifs."
    ),
    Niche.MOTIVATION: (
        "You are writing a short, powerful motivational narration "
        "for a 45-60 second vertical video. Focus on success stories, "
        "life lessons, or inspiring transformations."
    ),
    Niche.FINANCE: (
        "You are writing a short, insightful finance narration "
        "for a 45-60 second vertical video. Focus on money tips, "
        "investment stories, or financial lessons."
    ),
    Niche.TECH: (
        "You are writing a short, fascinating tech narration "
        "for a 45-60 second vertical video. Focus on emerging technology, "
        "AI developments, or tech industry stories."
    ),
}


# =============================================================================
# SERIES CONFIG (what users configure when creating a series)
# =============================================================================

@dataclass
class SeriesConfig:
    """
    Configuration for a video series.
    This is what gets stored in the database per series.
    """
    # Basic info
    name: str
    niche: Niche = Niche.TRUE_CRIME
    
    # Language
    language: Language = Language.ENGLISH
    
    # Content generation
    video_duration: VideoDuration = VideoDuration.MEDIUM
    beats_per_episode: int = 12  # Auto-set based on duration if not specified
    
    # Visual style
    art_style: ArtStyle = ArtStyle.COMIC_DARK
    custom_art_prompt: Optional[str] = None  # Override art_style if provided
    
    # Audio
    voice: VoiceOption = VoiceOption.ALLOY
    
    # Music
    music_mood: Optional[MusicMood] = MusicMood.DARK
    music_track_id: Optional[str] = None  # Specific track ID
    custom_music_url: Optional[str] = None  # User uploaded music
    music_volume: float = 0.10  # 0.0 to 1.0
    
    # Captions
    caption_style: CaptionStyle = CaptionStyle.RED_HIGHLIGHT
    
    # Motion
    motion_effect: MotionEffect = MotionEffect.KEN_BURNS
    
    # Posting schedule
    post_frequency: PostFrequency = PostFrequency.MANUAL
    post_time: str = "18:00"  # 24h format
    timezone: str = "UTC"
    
    # Platforms (which are enabled)
    post_to_tiktok: bool = False
    post_to_youtube: bool = False
    post_to_instagram: bool = False
    
    # Watermark (for free tier)
    add_watermark: bool = True
    
    def get_beats_count(self) -> int:
        """Get number of beats based on duration setting."""
        return DURATION_BEATS.get(self.video_duration, 12)
    
    def get_art_prompt(self) -> str:
        """Get the full art style prompt."""
        if self.custom_art_prompt:
            return self.custom_art_prompt
        return ART_STYLE_PROMPTS.get(self.art_style, ART_STYLE_PROMPTS[ArtStyle.COMIC_DARK])
    
    def get_niche_prompt(self) -> str:
        """Get the niche-specific story generation prompt."""
        return NICHE_PROMPTS.get(self.niche, NICHE_PROMPTS[Niche.TRUE_CRIME])


@dataclass
class EpisodeConfig:
    """
    Configuration for a single episode.
    Inherits from series but can override specific settings.
    """
    series_config: SeriesConfig
    topic: str
    
    # Optional overrides (None = use series default)
    caption_style_override: Optional[CaptionStyle] = None
    voice_override: Optional[VoiceOption] = None
    art_style_override: Optional[ArtStyle] = None
    
    @property
    def caption_style(self) -> CaptionStyle:
        return self.caption_style_override or self.series_config.caption_style
    
    @property
    def voice(self) -> VoiceOption:
        return self.voice_override or self.series_config.voice
    
    @property
    def art_style(self) -> ArtStyle:
        return self.art_style_override or self.series_config.art_style


# =============================================================================
# TIER LIMITS
# =============================================================================

@dataclass
class TierLimits:
    """Limits for each pricing tier."""
    max_series: int
    max_episodes_per_month: int
    auto_post_enabled: bool
    max_post_frequency: PostFrequency
    storage_days: int  # 0 = permanent
    watermark_required: bool
    available_voices: list[VoiceOption] = field(default_factory=list)
    available_art_styles: list[ArtStyle] = field(default_factory=list)
    available_caption_styles: list[CaptionStyle] = field(default_factory=list)


TIER_LIMITS = {
    "free": TierLimits(
        max_series=1,
        max_episodes_per_month=5,
        auto_post_enabled=False,
        max_post_frequency=PostFrequency.MANUAL,
        storage_days=7,
        watermark_required=True,
        available_voices=[VoiceOption.ALLOY, VoiceOption.NOVA],
        available_art_styles=[ArtStyle.COMIC_DARK, ArtStyle.REALISTIC],
        available_caption_styles=[CaptionStyle.RED_HIGHLIGHT, CaptionStyle.BOLD_STROKE],
    ),
    "hobby": TierLimits(
        max_series=3,
        max_episodes_per_month=30,
        auto_post_enabled=True,
        max_post_frequency=PostFrequency.THREE_PER_WEEK,
        storage_days=0,  # permanent
        watermark_required=False,
        available_voices=list(VoiceOption),
        available_art_styles=list(ArtStyle),
        available_caption_styles=list(CaptionStyle),
    ),
    "daily": TierLimits(
        max_series=5,
        max_episodes_per_month=60,
        auto_post_enabled=True,
        max_post_frequency=PostFrequency.DAILY,
        storage_days=0,
        watermark_required=False,
        available_voices=list(VoiceOption),
        available_art_styles=list(ArtStyle),
        available_caption_styles=list(CaptionStyle),
    ),
    "pro": TierLimits(
        max_series=10,
        max_episodes_per_month=120,
        auto_post_enabled=True,
        max_post_frequency=PostFrequency.TWICE_DAILY,
        storage_days=0,
        watermark_required=False,
        available_voices=list(VoiceOption),
        available_art_styles=list(ArtStyle),
        available_caption_styles=list(CaptionStyle),
    ),
}
