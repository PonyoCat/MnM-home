# League Dashboard - Production Deployment Guide

**Complete guide for deploying the MnM Dashboard to Render (backend) and Vercel (frontend) using free tiers.**

**Total Cost:** $0/month

---

## Prerequisites

Before starting deployment, ensure:
- [ ] Code is committed to a GitHub repository
- [ ] Backend `.env` file is NOT tracked in git (should be in `.gitignore`)
- [ ] Frontend builds successfully locally: `cd frontend && npm run build`
- [ ] You have a Neon PostgreSQL database with connection string ready
- [ ] You have accounts on Render.com and Vercel.com (free tier)

---

## Part 1: Deploy Backend to Render

### Step 1: Create New Web Service

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **New +** > **Web Service**
3. Select **Build and deploy from a Git repository**
4. Connect your GitHub account if not already connected
5. Find and select your `MnM-home` repository
6. Click **Connect**

### Step 2: Configure Service Settings

**Basic Settings:**
- **Name:** `mnm-dashboard-api` (or your preferred name)
- **Region:** Choose closest to your users (e.g., Frankfurt for EU)
- **Branch:** `main`
- **Root Directory:** `backend`

**Build Settings:**
- **Runtime:** Python 3
- **Build Command:**
  ```bash
  pip install -r requirements.txt
  ```
- **Start Command:**
  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port $PORT
  ```

**Instance Type:**
- Select **Free** (spins down after 15 min idle; ~1 min cold start)

### Step 3: Add Environment Variables

Click **Advanced** > **Add Environment Variable**:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | Your Neon connection string (see below) |

**Neon Connection String Format:**
```
postgresql+asyncpg://user:password@host/database?sslmode=require
```

Example:
```
postgresql+asyncpg://user:AbCd1234@ep-cool-sun-123456.eu-central-1.aws.neon.tech/neondb?sslmode=require
```

**IMPORTANT:**
- Use `postgresql+asyncpg://` (NOT `postgresql://`)
- Include `?sslmode=require` at the end
- Get this from your Neon dashboard > Connection Details

### Step 4: Deploy

1. Click **Create Web Service**
2. Wait for deployment to complete (3-5 minutes)
3. Render will show deployment logs in real-time
4. Once complete, you'll see "Deploy successful"

### Step 5: Test Backend

Your backend URL will be: `https://mnm-dashboard-api.onrender.com` (or your chosen name)

Test these endpoints:
- Root: `https://your-app.onrender.com/`
  - Should return: `{"message": "MnM Dashboard API", "status": "running", "version": "1.0.0"}`
- API Docs: `https://your-app.onrender.com/docs`
  - Should show FastAPI Swagger UI
- Session Review: `https://your-app.onrender.com/api/session-review`
  - Should return session review data

**Save your Render URL** - you'll need it for Vercel configuration.

---

## Part 2: Deploy Frontend to Vercel

### Step 1: Import Project

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **Add New...** > **Project**
3. Click **Import Git Repository**
4. Select your `MnM-home` repository
5. Click **Import**

### Step 2: Configure Build Settings

**Framework Preset:** Vite (should auto-detect)

**Root Directory:**
- Click **Edit**
- Enter: `frontend`
- Click **Continue**

**Build Settings:**
- **Build Command:** `npm run build` (auto-detected)
- **Output Directory:** `dist` (auto-detected)
- **Install Command:** `npm install` (auto-detected)

### Step 3: Add Environment Variables

Click **Environment Variables**:

| Key | Value | Environments |
|-----|-------|--------------|
| `VITE_API_URL` | Your Render backend URL | Production, Preview, Development |

**Example:**
```
VITE_API_URL=https://mnm-dashboard-api.onrender.com
```

**IMPORTANT:**
- NO trailing slash
- Use the exact URL from your Render deployment
- Select all three environments (Production, Preview, Development)

### Step 4: Deploy

1. Click **Deploy**
2. Wait for build to complete (2-3 minutes)
3. Vercel will show build logs in real-time
4. Once complete, you'll see "Ready" with a preview image

### Step 5: Get Your Vercel URL

After deployment completes:
- Your production URL will be: `https://mnm-dashboard.vercel.app` (or similar)
- Click **Visit** to open the deployed app
- You'll also get preview URLs for each deployment

**Save your exact Vercel domain** - you'll need it for CORS configuration.

---

## Part 3: Configure CORS Security

After both deployments are live, you need to update the backend to allow requests from your Vercel domain.

### Step 1: Update Backend CORS Settings

Edit `backend/app/main.py` and replace the `allow_origins` list:

**Before:**
```python
allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://*.vercel.app",  # Wildcard - not secure for production
],
```

**After:**
```python
allow_origins=[
    "http://localhost:5173",      # Keep for local dev
    "http://127.0.0.1:5173",      # Keep for local dev
    "https://mnm-dashboard.vercel.app",  # Replace with YOUR exact Vercel domain
    # "https://your-custom-domain.com",  # Optional: add custom domain if you have one
],
```

**IMPORTANT:**
- Replace `mnm-dashboard.vercel.app` with YOUR actual Vercel domain
- Keep localhost entries for local development
- Remove the wildcard `https://*.vercel.app` pattern
- Use exact domains only (no wildcards in production)

### Step 2: Commit and Push Changes

```bash
git add backend/app/main.py
git commit -m "Update CORS with production Vercel domain"
git push origin main
```

Render will automatically detect the push and redeploy your backend (auto-deploy is enabled by default).

### Step 3: Verify CORS Update

1. Wait for Render to finish redeploying (check dashboard)
2. Open your Vercel URL in a browser
3. Open browser DevTools (F12) > Console
4. Look for any CORS errors - there should be NONE
5. Check Network tab - API calls should show 200 status codes

---

## Part 4: Production Validation

Test all dashboard features to ensure everything works in production:

### Session Review
1. Open your Vercel URL
2. Navigate to Session Review section
3. Edit the notes, click Save
4. Refresh the page
5. **Verify:** Notes persist after refresh

### Weekly Champions
1. Go to Weekly Champions section
2. Toggle some checkboxes
3. Refresh the page
4. **Verify:** Selections persist after refresh

### Draft Notes
1. Open Draft Notes section
2. Edit and save the notes
3. Refresh the page
4. **Verify:** Changes persist after refresh

### Pick Stats
1. Go to Pick Stats section
2. Add a new champion
3. Click Win/Loss buttons to update stats
4. Refresh the page
5. **Verify:**
   - Champion appears in the list
   - Win/loss counts are correct
   - Win rate percentage is accurate

### Mobile Testing (Optional)
1. Open your Vercel URL on a mobile device
2. Test one CRUD operation (e.g., save session notes)
3. **Verify:** Layout is responsive and functional

### Multi-User Testing (Optional)
1. Share Vercel URL with teammates
2. Have multiple people make changes simultaneously
3. Refresh to see each other's updates
4. **Verify:** Data syncs correctly across users

---

## Part 5: Enable Auto-Deployments

Both platforms should have auto-deploy enabled by default:

### Render
- Auto-deploys are enabled automatically when connecting from Git
- Every push to `main` branch triggers a new deployment
- Check: Dashboard > Service > Settings > Build & Deploy
- **Verify:** "Auto-Deploy" is set to "Yes"

### Vercel
- Auto-deploys are enabled by default
- Every push to `main` triggers production deployment
- Every push to other branches creates preview deployments
- Check: Dashboard > Project > Settings > Git
- **Verify:** "Production Branch" is set to `main`

---

## Part 6: Monitor Free Tier Usage

### Render Free Tier Limits
- **Spin-down:** After 15 minutes of inactivity
- **Cold start:** ~60 seconds to wake up on first request
- **Hours:** 750 free instance hours per month
- **Bandwidth:** Limited monthly quota

**Recommendation:** If cold starts are unacceptable, implement the keep-alive service from `PRPs/keep-alive-service.md` using UptimeRobot (also free).

### Vercel Free Tier Limits
- **Bandwidth:** 100 GB/month
- **Builds:** 6000 minutes/month
- **Functions:** 100 GB-hours/month execution

**Note:** These limits are very generous for a small team dashboard.

### Neon Free Tier Limits
- **Storage:** 3 GB
- **Compute:** 191.9 hours/month active time
- **Branches:** 10 development branches

**Note:** The dashboard's data footprint is tiny; you'll stay well within limits.

---

## Troubleshooting

### Backend Issues

**Problem:** Render build fails
- **Check:** `requirements.txt` is complete
- **Check:** Root Directory is set to `backend`
- **Check:** Build command is `pip install -r requirements.txt`

**Problem:** Backend returns 500 errors
- **Check:** `DATABASE_URL` environment variable is set correctly
- **Check:** Connection string uses `postgresql+asyncpg://`
- **Check:** Connection string includes `?sslmode=require`
- **View:** Render logs (Dashboard > Logs) for error details

**Problem:** Slow first request
- **This is normal** - Free tier spins down after 15 min idle
- First request takes ~60 seconds to wake up
- **Solution:** Implement keep-alive service (optional)

### Frontend Issues

**Problem:** Vercel build fails
- **Check:** Root Directory is set to `frontend`
- **Check:** Build command is `npm run build`
- **Check:** Output directory is `dist`
- **View:** Vercel deployment logs for specific error

**Problem:** API calls fail with CORS errors
- **Check:** `VITE_API_URL` environment variable is set on Vercel
- **Check:** Backend `allow_origins` includes exact Vercel domain
- **Check:** No trailing slash in `VITE_API_URL`
- **Test:** Visit `https://your-backend.onrender.com/docs` directly

**Problem:** Environment variable not updating
- **Fix:** Redeploy frontend after changing env vars
- **Note:** Vercel requires rebuild to pick up env var changes

**Problem:** 404 on refresh (SPA routing issue)
- **Fix:** Create `vercel.json` in frontend root:
  ```json
  {
    "rewrites": [
      { "source": "/(.*)", "destination": "/" }
    ]
  }
  ```

### Database Issues

**Problem:** Connection timeouts
- **Check:** Neon project is active (not suspended)
- **Check:** Connection string is correct
- **Test:** Connect from local backend first

**Problem:** "relation does not exist" errors
- **Fix:** Run `python backend/init_db.py` to create tables
- **Note:** This should be done before first backend deployment

---

## Production URLs Checklist

After successful deployment, record your URLs:

- **Backend API:** `https://_____.onrender.com`
- **API Docs:** `https://_____.onrender.com/docs`
- **Frontend:** `https://_____.vercel.app`
- **Database:** Neon dashboard link

**Save these URLs** in `PROJECT_STATUS.md` for team reference.

---

## Optional Enhancements

### Custom Domain (Vercel)
1. Buy domain from registrar (Namecheap, Google Domains, etc.)
2. Vercel Dashboard > Project > Settings > Domains
3. Add custom domain and configure DNS records
4. Update CORS in backend with new domain

### Keep-Alive Service (Render)
1. Sign up for UptimeRobot (free)
2. Create HTTP monitor for your Render backend URL
3. Set check interval to 5 minutes
4. Prevents cold starts by pinging regularly
5. See `PRPs/keep-alive-service.md` for full guide

### Environment-Specific Builds (Vercel)
- Production: Uses `VITE_API_URL` from production env
- Preview: Can use different backend for testing
- Development: Can point to localhost

---

## Security Best Practices

1. **Never commit `.env` files** - Already in `.gitignore`
2. **Use exact CORS origins** - No wildcards in production
3. **Rotate database credentials** - If accidentally exposed
4. **Enable HTTPS only** - Both platforms enforce this by default
5. **Monitor logs** - Check for unusual activity

---

## Cost Breakdown

| Service | Tier | Monthly Cost |
|---------|------|--------------|
| Render (Backend) | Free | $0 |
| Vercel (Frontend) | Hobby | $0 |
| Neon (Database) | Free | $0 |
| UptimeRobot (Optional) | Free | $0 |
| **Total** | | **$0** |

**Upgrade Paths:**
- Render: $7/month for always-on (no spin-down)
- Vercel: $20/month for team features
- Neon: $19/month for more compute and storage

---

## Next Steps

1. **Deploy to production** using this guide
2. **Update PROJECT_STATUS.md** with production URLs
3. **Share with team** - Send Vercel URL to teammates
4. **Monitor usage** - Check free tier limits monthly
5. **Consider keep-alive** if cold starts are annoying

**Questions or Issues?**
- Check deployment logs on each platform
- Review the Troubleshooting section above
- Refer to `PRPs/deployment-hosting.md` for technical details
