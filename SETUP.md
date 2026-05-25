# TrainLoop — Setup Guide

## What you need

- A Supabase account (free): https://supabase.com
- An Anthropic API key: https://console.anthropic.com
- A Vercel account (free): https://vercel.com

---

## Step 1: Create a Supabase project

1. Go to https://supabase.com and create a new project
2. Open the **SQL Editor** and run these two files **in order**:
   - `supabase/migrations/001_schema.sql`
   - `supabase/migrations/002_seed_templates.sql`
3. In **Authentication > Providers**, enable **Google** (follow Supabase's Google OAuth guide)
4. Copy your project URL and anon key from **Settings > API**

## Step 2: Configure environment variables

Copy `.env.local.example` to `.env.local` and fill in:

```
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
ANTHROPIC_API_KEY=sk-ant-...
NEXT_PUBLIC_APP_URL=https://your-app.vercel.app
```

## Step 3: Run locally

```bash
npm install
npm run dev
```

Open http://localhost:3000

## Step 4: Deploy to Vercel

```bash
npx vercel
```

Add the same environment variables in the Vercel dashboard under **Settings > Environment Variables**.

---

## How to use as a trainer

1. **Register** an account at your deployed URL
2. **Create a course** and choose a question template
3. **Customize** your pre/post questions
4. **Activate** the course to get two shareable links
5. Send the **pre-course link** to participants before training
6. Run your training
7. Send the **post-course link** to participants after training
8. In the **Results** dashboard, click **Generate Analysis** to get AI insights
9. **Export PDF** to share with stakeholders

---

## Sharing with other trainers

Each trainer creates their own account. All data is isolated per trainer by Row-Level Security. No trainer can see another trainer's courses or responses.
