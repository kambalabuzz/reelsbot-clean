# ReelsBot - Automated Short-Form Video Generator

Generate TikTok/Reels/Shorts style videos with AI-generated scripts, images, voiceover, and karaoke-style captions.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Generate a video
python engine.py --topic "The Dyatlov Pass Incident" --caption-style beast --voice nova
```

## 📁 Project Structure

```
reelsbot/
├── engine.py           # Main entry point - orchestrates the pipeline
├── config.py           # All configurable options (styles, niches, tiers)
├── models.py           # Database models for SaaS version
├── cache_utils.py      # Cache management utilities
│
├── # GENERATION MODULES (all with caching!)
├── openai_utils.py     # Story beats + image generation (cached)
├── tts.py              # Text-to-speech (cached by script+voice)
├── alignment.py        # Whisper word alignment (cached by audio hash)
├── audio_utils.py      # Silence trimming (cached)
│
├── # VIDEO ASSEMBLY
├── assemble.py         # Combine images + audio + motion effects
├── captions.py         # 10+ caption style presets
├── broll.py            # Stock video fetching (Pexels)
│
├── # CACHE DIRECTORIES
├── cache/
│   ├── beats/          # Story beat scripts
│   ├── audio/          # Raw TTS audio
│   ├── trimmed_audio/  # Silence-removed audio
│   └── alignment/      # Word timing JSON
├── media_cache/        # Generated images
│
├── # OUTPUT
├── outputs/            # Generated videos
│
├── # ASSETS
├── assets/
│   └── music/          # Background music files
└── templates/          # Video templates (JSON configs)
```

## ⚙️ Configurable Options

### Caption Styles (`--caption-style`)

| Style | Description |
|-------|-------------|
| `red_highlight` | Red glow on active word, white others |
| `karaoke` | Purple box highlight (classic TikTok) |
| `beast` | MrBeast style - chunky yellow highlight |
| `majestic` | Elegant gold on white |
| `bold_stroke` | Heavy black outline |
| `sleek` | Modern minimal, gray context words |
| `elegant` | Thin serif, sophisticated |
| `neon` | Cyberpunk pink/cyan glow |
| `fire` | Orange/red highlight |
| `hormozi` | Alex Hormozi style - 2 words, big pop |

### Voices (`--voice`)

| Voice | Style |
|-------|-------|
| `alloy` | Neutral, versatile |
| `echo` | Warm, conversational |
| `fable` | British, storyteller |
| `onyx` | Deep, authoritative |
| `nova` | Energetic, young |
| `shimmer` | Soft, gentle |

### Art Styles (`--art-style`)

| Style | Description |
|-------|-------------|
| `comic_dark` | Dark true-crime comic style |
| `comic_bright` | Vibrant pop art comic |
| `realistic` | Photorealistic digital art |
| `anime` | Anime/Ghibli style |
| `noir` | Black & white film noir |
| `watercolor` | Soft watercolor painting |
| `pixel_art` | 16-bit retro gaming |
| `oil_painting` | Classical oil painting |
| `sketch` | Pencil sketch style |
| `cyberpunk` | Neon cyberpunk aesthetic |

### Content Niches (`--niche`)

| Niche | Focus |
|-------|-------|
| `true_crime` | Unsolved cases, mysteries |
| `horror` | Creepy encounters, terror |
| `mystery` | Puzzles, strange occurrences |
| `history` | Historical events, facts |
| `conspiracy` | Conspiracy theories |
| `paranormal` | Ghosts, UFOs, supernatural |
| `sci_fi` | Futuristic, space |
| `motivation` | Success stories, inspiration |
| `finance` | Money tips, investing |
| `tech` | Technology, AI |

### Motion Effects (`--motion`)

| Effect | Description |
|--------|-------------|
| `ken_burns` | Slow zoom/pan (default) |
| `static` | No movement |
| `zoom_pulse` | Rhythmic zoom pulse |
| `shake` | Subtle handheld shake |
| `parallax` | Layered drift effect |

## 🎬 Usage Examples

### Basic Generation
```bash
python engine.py --topic "The Zodiac Killer" 
```

### Full Customization
```bash
python engine.py \
  --topic "The Bermuda Triangle Mystery" \
  --caption-style beast \
  --voice onyx \
  --art-style noir \
  --niche mystery \
  --beats 10 \
  --watermark
```

### Using Config Objects (Python)
```python
from engine import generate_episode
from config import SeriesConfig, CaptionStyle, VoiceOption, ArtStyle, Niche

# Create a series config
config = SeriesConfig(
    name="Dark History",
    niche=Niche.HISTORY,
    art_style=ArtStyle.NOIR,
    voice=VoiceOption.ONYX,
    caption_style=CaptionStyle.BEAST,
    beats_per_episode=10,
)

# Generate an episode
result = generate_episode(
    topic="The Dancing Plague of 1518",
    series_config=config,
)

print(f"Video ready: {result['final_video']}")
```

## 🔧 Files to Edit for Features

### To Add a New Caption Style
1. Edit `captions.py` → Add to `STYLES` dict

### To Add a New Art Style
1. Edit `config.py` → Add to `ArtStyle` enum
2. Edit `config.py` → Add prompt to `ART_STYLE_PROMPTS`

### To Add a New Niche
1. Edit `config.py` → Add to `Niche` enum
2. Edit `config.py` → Add prompt to `NICHE_PROMPTS`
3. Edit `openai_utils.py` → Add to `NICHE_SYSTEM_PROMPTS`

### To Add a New Voice
1. Edit `config.py` → Add to `VoiceOption` enum

### To Add a New Motion Effect
1. Edit `assemble.py` → Add function `_apply_<effect>`
2. Edit `assemble.py` → Add to `MOTION_EFFECTS` dict
3. Edit `config.py` → Add to `MotionEffect` enum

## 📊 Database Schema (SaaS)

See `models.py` for full SQLAlchemy models. Key tables:

- **users** - Auth, subscription tier, usage
- **series** - User's video series with all settings
- **episodes** - Individual generated videos
- **social_accounts** - Connected TikTok/YouTube/IG
- **posts** - Tracking what's posted where
- **music_tracks** - Background music library
- **render_jobs** - Queue management

## 🚀 Roadmap to SaaS

### Phase 1: Pipeline (DONE ✅)
- [x] Script generation
- [x] Image generation with caching
- [x] TTS with silence trimming
- [x] Word-level alignment
- [x] 10+ caption styles
- [x] Multiple art styles
- [x] Multiple niches
- [x] Motion effects
- [x] Config system

### Phase 2: Basic SaaS Shell
- [ ] FastAPI backend
- [ ] Database setup (PostgreSQL)
- [ ] Next.js dashboard
- [ ] Auth (Clerk)
- [ ] Create series wizard
- [ ] Episode status tracking

### Phase 3: Scheduling + Auto-post
- [ ] Cron scheduler
- [ ] TikTok OAuth + posting
- [ ] YouTube OAuth + posting
- [ ] Instagram Graph API

### Phase 4: Payments + Polish
- [ ] Stripe subscriptions
- [ ] Tier limits enforcement
- [ ] Usage tracking
- [ ] Error handling
- [ ] Email notifications

## 💰 Pricing Tiers

| Tier | Series | Episodes/mo | Auto-post | Storage | Price |
|------|--------|-------------|-----------|---------|-------|
| Free | 1 | 5 | No | 7 days | $0 |
| Hobby | 3 | 30 | 3x/week | Forever | $29 |
| Daily | 5 | 60 | Daily | Forever | $49 |
| Pro | 10 | 120 | 2x/day | Forever | $99 |

## 💾 Caching (Save Money!)

All expensive API calls are cached to avoid wasting credits:

| Asset | Cache Location | What's Cached |
|-------|----------------|---------------|
| Story beats | `cache/beats/` | Script + visuals by topic+niche |
| TTS Audio | `cache/audio/` | Audio by script+voice hash |
| Trimmed Audio | `cache/trimmed_audio/` | Silence-removed audio |
| Alignment | `cache/alignment/` | Word timings by audio hash |
| Images | `media_cache/` | Generated images by prompt |

### Cache Commands

```bash
# View cache stats
python cache_utils.py stats

# Clear all caches
python cache_utils.py clear

# Clear specific cache
python cache_utils.py clear images

# Clear files older than 7 days
python cache_utils.py old 7
```

### Re-running Same Topic = FREE

If you run the same topic twice with same settings, everything comes from cache:
```bash
python engine.py --topic "The Dyatlov Pass"  # First run: ~$0.50
python engine.py --topic "The Dyatlov Pass"  # Second run: $0.00 (all cached!)
```

Only changing voice/art style/captions will regenerate those specific assets.

## 🔑 Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional
OPENAI_MODEL=gpt-4o-mini
OPENAI_IMAGE_MODEL=gpt-image-1
PEXELS_API_KEY=...  # For B-roll

# Future (SaaS)
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
CLERK_SECRET_KEY=...
STRIPE_SECRET_KEY=...
```

## 📝 License

MIT
