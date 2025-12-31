# 🎬 ReelsBot - AI Video Generation Platform

**Clean, industry-standard architecture for automated TikTok/Reels video generation**

[![Deployed](https://img.shields.io/badge/status-deployed-success)](https://frontend-f8trd38ta-kambalabuzzs-projects.vercel.app)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## ✨ Features

### 🎯 Core Capabilities
- **Director Mode** - One-off videos on any topic
- **Series Mode** - Automated recurring episodes
- **11 Caption Styles** - Including the new **Storyteller** style for mystery/documentary
- **State Persistence** - Resume video generation after navigating away
- **Real-time Polling** - Live progress updates every 3 seconds

### 🎨 Storyteller Caption Style (NEW!)
Perfect for mystery, documentary, and true crime videos:
- Yellow word highlighting (#FFFF00)
- White inactive words (#FFFFFF)
- Heavy black stroke (8px) for readability
- 110px Montserrat Black font
- 1-2 words per line for dramatic pacing

### 🔧 Technical Features
- **Clean Architecture** - Separate frontend/api/worker
- **Atomic Job Locking** - PostgreSQL-based assembly queue
- **Better Error Handling** - OpenAI quota and rate limit warnings
- **Auto-Resume** - localStorage-based state persistence (10min timeout)

---

## 🚀 Live Deployment

| Service | URL | Status |
|---------|-----|--------|
| **Frontend** | https://frontend-f8trd38ta-kambalabuzzs-projects.vercel.app | ✅ Live |
| **API** | https://reelsbot-api-3049360670.us-central1.run.app | ✅ Live |
| **Worker** | https://reelsbot-worker-3049360670.us-central1.run.app | ✅ Live |
| **Database** | https://ehwjfelgzoaelgiziqsk.supabase.co | ✅ Live |

---

## 📁 Project Structure

```
reelsbot-clean/
├── frontend/              # Next.js 14 (Vercel)
│   ├── app/
│   │   └── dashboard/
│   │       ├── create/    # Director Mode with state persistence
│   │       ├── series/    # Series management
│   │       └── videos/    # Video library
│   ├── components/        # React components
│   ├── vercel.json        # Deployment config
│   └── package.json       # Next.js 14.2.28
│
├── api/                   # FastAPI (Cloud Run)
│   ├── main.py            # Routes and endpoints
│   ├── video_engine.py    # Video generation logic
│   ├── Dockerfile
│   └── requirements.txt
│
├── worker/                # Video assembly (Cloud Run)
│   ├── queue_worker.py    # Job polling loop
│   ├── viral_pipeline.py  # Video assembly
│   ├── captions.py        # Caption styles (storyteller at line 255)
│   ├── Dockerfile
│   └── requirements.txt
│
└── database/              # Supabase SQL
    ├── nuclear_clean.sql  # Fresh schema installation
    └── fresh_schema.sql   # Alternative install
```

---

## 🛠️ Tech Stack

### Frontend
- **Next.js 14** - App Router with Server Components
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn/ui** - Component library
- **Clerk** - Authentication
- **Vercel** - Hosting

### Backend
- **FastAPI** - Python async API framework
- **Supabase** - PostgreSQL database
- **Google Cloud Run** - Containerized microservices
- **OpenAI API** - Script generation & TTS
- **Replicate API** - Image generation
- **ElevenLabs** - Alternative voice generation

### Worker
- **FFmpeg** - Video assembly
- **MoviePy** - Python video editing
- **ASS Subtitles** - Advanced caption styling
- **PostgreSQL** - Atomic job queue with locking

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- Docker (for local worker development)
- Supabase account
- Google Cloud account (for deployment)

### 1. Clone Repository
```bash
git clone https://github.com/kambalabuzz/reelsbot-clean.git
cd reelsbot-clean
```

### 2. Setup Database
1. Go to [Supabase SQL Editor](https://ehwjfelgzoaelgiziqsk.supabase.co/project/_/sql)
2. Run `database/nuclear_clean.sql`

### 3. Setup Frontend
```bash
cd frontend
cp .env.example .env.local
# Add your Clerk keys to .env.local
npm install
npm run dev
```

Open http://localhost:3000

### 4. Setup API
```bash
cd api
cp .env.example .env
# Add your API keys to .env
pip install -r requirements.txt
uvicorn main:app --reload
```

API runs at http://localhost:8080

### 5. Setup Worker
```bash
cd worker
cp .env.example .env
# Add your API keys to .env
pip install -r requirements.txt
python queue_worker.py
```

---

## 📦 Deployment

### Frontend (Vercel)
```bash
cd frontend
vercel --prod
```

### API (Cloud Run)
```bash
cd api
gcloud run deploy reelsbot-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

### Worker (Cloud Run)
```bash
cd worker
gcloud run deploy reelsbot-worker \
  --source . \
  --region us-central1 \
  --memory 4Gi \
  --cpu 4 \
  --timeout 900
```

See [DEPLOY.md](DEPLOY.md) for detailed deployment instructions.

---

## 🎨 Caption Styles

Choose from 11 caption styles:

1. **storyteller** ⭐ NEW - Mystery/Documentary style
2. **red_highlight** - Red glow on active word
3. **karaoke** - Purple box highlight (TikTok classic)
4. **beast** - MrBeast style with big yellow pops
5. **majestic** - Clean elegant white
6. **bold_stroke** - Heavy outline
7. **sleek** - Modern minimal
8. **elegant** - Thin serif
9. **neon** - Cyberpunk glow
10. **fire** - Orange/red gradient
11. **hormozi** - Alex Hormozi big pops

---

## 🧪 Testing

### Test Video Generation
1. Go to https://frontend-f8trd38ta-kambalabuzzs-projects.vercel.app
2. Click "AI Director"
3. Generate a video:
   - Topic: "The mysterious disappearance at Dyatlov Pass"
   - Voice: Adam
   - Art Style: Cinematic
   - Caption Style: **Storyteller**

Expected: 30-60 second video with yellow word highlighting

### Test State Persistence
1. Start video generation
2. Navigate to "Series" page
3. Wait 10 seconds
4. Return to "AI Director"
5. Expected: Toast "Resumed previous generation"

---

## 📊 Database Schema

### Tables
- `director_videos` - One-off videos from Director Mode
- `episodes` - Series episodes
- `series` - Series configuration
- `assembly_jobs` - Video assembly queue
- `social_accounts` - Connected platforms

### Key Functions
- `claim_assembly_job(worker_id, lock_seconds)` - Atomic job locking
- `update_series_stats()` - Auto-update series statistics

---

## 🔑 Environment Variables

### Frontend (.env.local)
```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_clerk_key
CLERK_SECRET_KEY=your_clerk_secret
```

### API & Worker (.env)
```env
# Database
SUPABASE_URL=https://ehwjfelgzoaelgiziqsk.supabase.co
SUPABASE_KEY=your_service_role_key

# AI Services
OPENAI_API_KEY=your_openai_key
ELEVENLABS_API_KEY=your_elevenlabs_key
REPLICATE_API_TOKEN=your_replicate_token
```

---

## 📝 Key Files

### Frontend
- [app/dashboard/create/page.tsx](frontend/app/dashboard/create/page.tsx) - Director Mode with state persistence
- [vercel.json](frontend/vercel.json) - API proxy configuration

### Worker
- [captions.py](worker/captions.py#L255) - Storyteller caption style
- [viral_pipeline.py](worker/viral_pipeline.py) - Video assembly logic
- [queue_worker.py](worker/queue_worker.py) - Job polling

### Database
- [nuclear_clean.sql](database/nuclear_clean.sql) - Fresh schema installation

---

## 🚨 Important Notes

### OpenAI API Credits Required
All voices use OpenAI TTS. Add credits at:
https://platform.openai.com/account/billing

**Recommended**: $20 (covers ~400-800 videos)

### Video Processing Time
Typical assembly: 2-5 minutes depending on:
- Number of images (8-15)
- Audio length (30-60 seconds)
- Caption complexity

---

## 📈 Monitoring

### API Logs
```bash
gcloud run services logs read reelsbot-api --region us-central1 --limit 50
```

### Worker Logs
```bash
gcloud run services logs read reelsbot-worker --region us-central1 --limit 50
```

### Database Status
```sql
SELECT 'Director Videos: ' || COUNT(*)::text FROM director_videos;
SELECT 'Pending Jobs: ' || COUNT(*)::text FROM assembly_jobs WHERE status = 'pending';
```

---

## 🤝 Contributing

This is a clean, production-ready codebase. Contributions welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

---

## 🙏 Acknowledgments

- Built with [Claude Code](https://claude.com/claude-code)
- Inspired by viral TikTok/Reels automation platforms
- Storyteller caption style perfect for mystery/documentary content

---

## 📞 Support

**Documentation**:
- [DEPLOYMENT_COMPLETE.md](DEPLOYMENT_COMPLETE.md) - Full deployment guide
- [DEPLOY.md](DEPLOY.md) - Deployment instructions
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Architecture overview

**Issues**: https://github.com/kambalabuzz/reelsbot-clean/issues

---

**Status**: 🎉 PRODUCTION READY

All services deployed and operational. Ready to generate mystery/documentary videos with storyteller captions!

**Live Demo**: https://frontend-f8trd38ta-kambalabuzzs-projects.vercel.app
