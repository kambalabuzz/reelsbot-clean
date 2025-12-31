# ReelsBot Deployment Guide

## Overview
This is the clean, production-ready ReelsBot codebase. All components are deployable independently.

## Project Structure
```
reelsbot-clean/
├── frontend/     # Next.js frontend (deploy to Vercel)
├── api/          # FastAPI backend (deploy to Render/Cloud Run)
├── worker/       # Video assembly worker (deploy to Render/Cloud Run)
└── database/     # Database schema files (apply to Supabase)
```

## 1. Database Setup

### Apply Schema
1. Go to Supabase Dashboard > SQL Editor
2. Run `database/schema.sql` first
3. Then run `database/database_migration_v2_fixed.sql`

### Required Tables
- director_videos
- episodes
- assembly_jobs
- videos

### Required Functions
- claim_assembly_job (for worker job claiming)

## 2. Frontend Deployment (Vercel)

### Prerequisites
- Vercel account
- Clerk account for authentication

### Steps
```bash
cd frontend
npm install
npm run build  # Test build locally

# Deploy to Vercel
vercel --prod
```

### Environment Variables (Vercel Dashboard)
```
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_xxx
CLERK_SECRET_KEY=sk_test_xxx
NEXT_PUBLIC_API_URL=https://your-api.onrender.com
```

### Update vercel.json
Edit `frontend/vercel.json` line 60:
```json
"destination": "https://your-actual-api-domain.onrender.com/api/:path*"
```

### Verification
- Build should succeed
- Next.js 14.2.28 is in dependencies
- No "No Next.js version detected" error

## 3. API Deployment (Render)

### Prerequisites
- Render account
- Supabase credentials
- OpenAI API key
- Replicate API token
- ElevenLabs API key

### Steps
1. Create new Web Service on Render
2. Connect to your repo
3. Root Directory: `api`
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Environment Variables (Render Dashboard)
```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJxxx
OPENAI_API_KEY=sk-xxx
REPLICATE_API_TOKEN=r8_xxx
ELEVENLABS_API_KEY=xxx
PORT=8080
PYTHONUNBUFFERED=1
```

### Docker Deployment (Alternative)
```bash
cd api
docker build -t reelsbot-api .
docker run -p 8080:8080 --env-file .env reelsbot-api
```

## 4. Worker Deployment (Render)

### Prerequisites
- Same as API
- Must deploy AFTER API is running

### Steps
1. Create new Web Service on Render
2. Connect to your repo
3. Root Directory: `worker`
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `python queue_worker.py`

### Environment Variables (Render Dashboard)
```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJxxx
OPENAI_API_KEY=sk-xxx
REPLICATE_API_TOKEN=r8_xxx
ELEVENLABS_API_KEY=xxx
WORKER_ID=assembly-worker-1
ASSEMBLY_POLL_SECONDS=5
ASSEMBLY_LOCK_SECONDS=900
WORKER_MODE=service
PORT=8080
PYTHONUNBUFFERED=1
```

### Docker Deployment (Alternative)
```bash
cd worker
docker build -t reelsbot-worker .
docker run --env-file .env reelsbot-worker
```

## 5. Verification Checklist

### Frontend
- [ ] Build succeeds with no errors
- [ ] Next.js version 14.2.28 is installed
- [ ] Vercel deployment shows "Ready"
- [ ] Can access dashboard at your-app.vercel.app
- [ ] Clerk authentication works

### API
- [ ] Service starts without errors
- [ ] Health check endpoint responds
- [ ] Can create director videos
- [ ] Can query videos from database
- [ ] API logs show no connection errors

### Worker
- [ ] Worker starts and logs "Worker started"
- [ ] Worker claims assembly jobs from database
- [ ] Video assembly completes successfully
- [ ] Captions render with storyteller style
- [ ] State persistence works (resume after crash)

### Integration
- [ ] Frontend can call API endpoints
- [ ] API can create assembly jobs
- [ ] Worker picks up and processes jobs
- [ ] Videos appear in frontend dashboard
- [ ] Download/preview works

## Common Issues

### Frontend: "No Next.js version detected"
✅ FIXED: Next.js 14.2.28 is in dependencies

### Frontend: Build fails
- Clear node_modules and package-lock.json
- Run `npm install` fresh
- Check Node version (need v18+)

### API: Database connection fails
- Verify SUPABASE_URL and SUPABASE_KEY
- Check Supabase project is not paused
- Verify RLS policies allow service role access

### Worker: No jobs claimed
- Check database has claim_assembly_job function
- Verify assembly_jobs table exists
- Check worker logs for errors
- Ensure WORKER_MODE=service (not "job")

### Worker: Video assembly fails
- Check all API keys are valid
- Verify FFmpeg is available (included in Docker image)
- Check OpenAI quota not exceeded
- Verify image URLs are accessible

## Features Included

### Frontend
- Next.js 14.2.28
- Clerk authentication
- Dashboard with video management
- Proper vercel.json configuration
- All UI components working

### API
- FastAPI with all endpoints
- Director video creation
- Assembly job management
- Status/retry endpoints
- ElevenLabs voice generation

### Worker
- State persistence (resume processing)
- Storyteller caption style
- TikTok-style 2-word chunks
- Color animation on captions
- Retry logic with backoff
- Job claiming with locks

### Database
- Separate tables for director videos and series
- Assembly jobs queue system
- Proper RPC functions
- Migration scripts included

## Next Steps

1. Deploy database schema to Supabase
2. Deploy API to Render (get URL)
3. Update frontend vercel.json with API URL
4. Deploy frontend to Vercel
5. Deploy worker to Render
6. Test end-to-end video creation

## Support

If you encounter issues:
1. Check service logs in Render/Vercel dashboard
2. Verify all environment variables are set
3. Test API endpoints with curl/Postman
4. Check Supabase logs for database errors
