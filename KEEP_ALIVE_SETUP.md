# Keep-Alive Service Setup Guide

**Purpose:** Prevent Render free tier backend from spinning down after 15 minutes of inactivity.

**Status:** ✅ IMPLEMENTED (GitHub Actions)

**Last Updated:** January 5, 2026

---

## Prerequisites

Before setting up keep-alive:
- [x] Backend code complete
- [x] Database configured (Neon)
- [x] **Backend deployed to Render** ✅ COMPLETE
- [x] **Production backend URL obtained** ✅ COMPLETE

**Current Status:** Backend is deployed at `https://mnm-home.onrender.com/`

**Implementation:** GitHub Actions workflow created at `.github/workflows/keep-alive.yml`

---

## Quick Setup (5 Minutes)

### Option 1: UptimeRobot (Recommended)

**Why Recommended:**
- Most popular and reliable
- Includes uptime monitoring
- Email alerts if backend crashes
- Free forever
- 5-minute ping interval (keeps backend awake)

**Setup Steps:**

1. **Create Account**
   - Go to https://uptimerobot.com/signUp
   - Sign up with email (free account)
   - Verify email address

2. **Add Monitor**
   - Click "Add New Monitor" button
   - Configure monitor:
     ```
     Monitor Type: HTTP(s)
     Friendly Name: MnM Dashboard Backend
     URL: https://YOUR-APP.onrender.com/
     Monitoring Interval: 5 minutes
     ```
   - Replace `YOUR-APP.onrender.com` with your actual Render URL
   - Click "Create Monitor"

3. **Verify Setup**
   - Monitor should show "Up" status immediately
   - Check "Events" tab to see ping history
   - Backend will now be pinged every 5 minutes

4. **Optional: Configure Alerts**
   - Go to "Alert Contacts"
   - Add your email for downtime notifications
   - Assign to the MnM Dashboard monitor

**Done!** Backend will never sleep again.

---

### Option 2: Cron-Job.org (More Precise Timing)

**Why Consider This:**
- More precise timing (14-minute interval)
- Less unnecessary requests than 5-minute interval
- Still completely free

**Setup Steps:**

1. **Create Account**
   - Go to https://cron-job.org
   - Create free account

2. **Create Cron Job**
   - Click "Create cronjob"
   - Configure job:
     ```
     Title: MnM Dashboard Keep-Alive
     URL: https://YOUR-APP.onrender.com/
     Schedule: */14 * * * * (every 14 minutes)
     Request method: GET
     ```
   - Enable the job
   - Save

3. **Verify**
   - Check execution history after 14 minutes
   - Backend should respond with 200 OK

---

### Option 3: GitHub Actions (For Developers)

**Why Consider This:**
- Integrated with codebase
- No external service needed
- Free for public repos

**Setup Steps:**

1. **Create Workflow File**

Create `.github/workflows/keep-alive.yml`:

```yaml
name: Keep Backend Alive

on:
  schedule:
    # Run every 14 minutes
    - cron: '*/14 * * * *'
  workflow_dispatch: # Allow manual trigger

jobs:
  keep-alive:
    runs-on: ubuntu-latest
    steps:
      - name: Ping Backend
        run: |
          echo "Pinging backend to prevent spin-down..."
          curl -f https://YOUR-APP.onrender.com/ || echo "Ping failed"
          echo "Ping completed at $(date)"
```

2. **Update Backend URL**
   - Replace `YOUR-APP.onrender.com` with your actual Render URL

3. **Commit and Push**
   ```bash
   git add .github/workflows/keep-alive.yml
   git commit -m "Add keep-alive GitHub Action"
   git push origin main
   ```

4. **Verify**
   - Go to your repo > Actions tab
   - Should see "Keep Backend Alive" workflow
   - Will run every 14 minutes automatically

**Note:** Requires your repository to be public for free tier GitHub Actions.

---

## Validation Checklist

After setting up keep-alive service:

- [ ] Wait 20 minutes without accessing the dashboard
- [ ] Visit your dashboard URL: `https://YOUR-FRONTEND.vercel.app`
- [ ] **Expected:** Instant response (no 30-second cold start)
- [ ] Check monitoring service dashboard for successful pings
- [ ] Verify email alerts work (if configured)

---

## Troubleshooting

### Monitor Shows "Down"

**Possible Causes:**
- Backend deployment failed on Render
- Database connection issues
- Render service suspended

**Solutions:**
1. Check Render dashboard for deployment status
2. Check Render logs for errors
3. Verify DATABASE_URL is set correctly
4. Test backend URL directly in browser

### Backend Still Sleeping

**Possible Causes:**
- Monitor interval too long (>15 min)
- Monitor not enabled
- Wrong backend URL

**Solutions:**
1. Verify monitor is enabled and running
2. Check ping interval is 5-14 minutes
3. Confirm exact backend URL (no typos)
4. Check monitor execution history

### Too Many Requests

**Symptoms:**
- Render shows high request volume
- Unnecessary bandwidth usage

**Solution:**
- Don't use multiple keep-alive services simultaneously
- Use 14-minute interval instead of 5-minute (if acceptable)
- Consider if cold starts are really a problem for your use case

---

## Cost Analysis

| Service | Monthly Cost | Ping Interval |
|---------|--------------|---------------|
| UptimeRobot | $0 | 5 minutes |
| Cron-Job.org | $0 | 14 minutes |
| GitHub Actions | $0 (public repo) | 14 minutes |

**Monthly Request Volume:**
- 5-minute interval: ~8,640 requests/month
- 14-minute interval: ~3,085 requests/month

**Render Free Tier:** 750 instance hours/month (sufficient for 24/7 uptime)

---

## When to Skip Keep-Alive

Consider NOT setting up keep-alive if:
- Your team only uses the dashboard during certain hours
- 30-second cold start is acceptable
- You want to minimize resource usage
- You plan to upgrade to Render paid tier ($7/month for always-on)

---

## Backend URL Reference

**Production URLs:**

```
Backend URL: https://mnm-home.onrender.com
Frontend URL: https://mnm-dashboard-frontend.onrender.com
```

The keep-alive service pings the backend URL every 14 minutes.

---

## Next Steps

1. **Deploy backend to Render** using [DEPLOYMENT.md](DEPLOYMENT.md)
2. **Obtain production backend URL** from Render dashboard
3. **Choose keep-alive option** (recommended: UptimeRobot)
4. **Complete 5-minute setup** following steps above
5. **Validate** using checklist
6. **Update [PROJECT_STATUS.md](PROJECT_STATUS.md)** with completion status

---

## Quick Reference Commands

### Test Backend Endpoint
```bash
# Replace with your actual URL
curl https://YOUR-APP.onrender.com/

# Expected response:
# {"message":"MnM Dashboard API","status":"running","version":"1.0.0"}
```

### Check API Docs
```bash
# Open in browser
https://YOUR-APP.onrender.com/docs
```

---

## Implementation Status

- [x] PRP reviewed and understood
- [x] Setup guide created
- [x] Options documented
- [x] **Backend deployed to Render** ✅ COMPLETE
- [x] **Keep-alive service configured** ✅ GitHub Actions (Option 3)
- [ ] **Validation pending** ⬅️ NEXT STEP (after push to GitHub)

**Status:** GitHub Actions workflow created. Push to GitHub to activate!
