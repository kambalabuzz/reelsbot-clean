# ReelsBot - Clean Architecture

## Directory Structure

```
reelsbot-clean/
├── frontend/                 # Next.js frontend (Vercel)
│   ├── app/                 # Next.js app directory
│   ├── components/          # React components
│   ├── lib/                 # Utilities
│   ├── public/              # Static assets
│   ├── package.json
│   ├── next.config.js
│   └── vercel.json
│
├── api/                     # FastAPI backend (Cloud Run)
│   ├── routes/              # API routes
│   ├── services/            # Business logic
│   ├── models/              # Pydantic models
│   ├── main.py              # FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
│
├── worker/                  # Video assembly worker (Cloud Run)
│   ├── viral_pipeline.py    # Main assembly logic
│   ├── captions.py          # Caption generation
│   ├── queue_worker.py      # Job queue processor
│   ├── requirements.txt
│   └── Dockerfile
│
├── database/                # Database schema & migrations
│   ├── schema.sql           # Complete schema
│   ├── migrations/          # Migration files
│   └── seed.sql             # Sample data
│
└── docs/                    # Documentation
    ├── API.md               # API documentation
    ├── DEPLOYMENT.md        # Deploy guide
    └── FEATURES.md          # Feature list
```

## Technology Stack

**Frontend:**
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- Clerk (Auth)
- Vercel (Hosting)

**Backend:**
- FastAPI (Python)
- Supabase (PostgreSQL)
- Cloud Run (Hosting)

**Worker:**
- Python
- FFmpeg
- MoviePy
- Cloud Run (Hosting)

**Storage:**
- Supabase Storage (Videos, Audio, Images)

## Clean Deployment

Each component deploys independently:
- `frontend/` → Vercel
- `api/` → Cloud Run (reelsbot-api)
- `worker/` → Cloud Run (reelsbot-worker)
