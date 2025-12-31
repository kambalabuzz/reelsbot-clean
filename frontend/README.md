# ReelsBot Frontend

Next.js 14 dashboard for the ReelsBot video generation platform.

## Quick Start

```bash
# Install dependencies
npm install

# Copy env file
cp .env.example .env.local

# Add your Clerk keys to .env.local
# Get them from https://clerk.com

# Run dev server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Tech Stack

- **Next.js 14** - App Router
- **Tailwind CSS** - Styling
- **shadcn/ui** - Components
- **Clerk** - Authentication
- **Framer Motion** - Animations
- **Zustand** - State management

## Project Structure

```
frontend/
├── app/
│   ├── page.tsx                    # Landing page
│   ├── layout.tsx                  # Root layout
│   ├── globals.css                 # Global styles
│   ├── sign-in/                    # Auth pages
│   ├── sign-up/
│   └── dashboard/
│       ├── layout.tsx              # Dashboard layout with sidebar
│       ├── page.tsx                # Dashboard home
│       ├── series/
│       │   ├── page.tsx            # Series list
│       │   └── create/
│       │       ├── page.tsx        # Series wizard
│       │       └── steps/          # Wizard steps
│       ├── videos/
│       │   └── page.tsx            # Videos list
│       ├── settings/
│       │   └── page.tsx            # User settings
│       └── billing/
│           └── page.tsx            # Billing & pricing
├── components/
│   └── ui/                         # shadcn components
├── lib/
│   └── utils.ts                    # Utilities
└── middleware.ts                   # Auth middleware
```

## Pages

| Route | Description |
|-------|-------------|
| `/` | Landing page |
| `/sign-in` | Sign in |
| `/sign-up` | Sign up |
| `/dashboard` | Dashboard home |
| `/dashboard/series` | Series list |
| `/dashboard/series/create` | Create series wizard |
| `/dashboard/videos` | All videos |
| `/dashboard/settings` | User settings |
| `/dashboard/billing` | Subscription & billing |

## Series Creation Wizard

8-step wizard matching FacelessReels:

1. **Niche** - Content category
2. **Voice** - Language & voice persona
3. **Music** - Background music selection
4. **Art Style** - Visual style (25+ options)
5. **Captions** - Caption style (10 options)
6. **Social** - Connect TikTok/IG/YouTube
7. **Schedule** - Duration, frequency, timing
8. **Review** - Final confirmation

## Environment Variables

```env
# Required
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
CLERK_SECRET_KEY=

# Optional (for full features)
NEXT_PUBLIC_API_URL=
STRIPE_SECRET_KEY=
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=
```

## Deployment

Deploy to Vercel:

```bash
npm install -g vercel
vercel
```

## Connecting to Backend

The frontend expects a backend API at `NEXT_PUBLIC_API_URL`. 

API endpoints needed:
- `POST /api/series` - Create series
- `GET /api/series` - List series
- `POST /api/episodes` - Generate episode
- `GET /api/videos` - List videos
- `POST /api/social/connect` - OAuth flow
- `POST /api/webhooks/stripe` - Stripe webhooks
