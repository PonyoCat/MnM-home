# Keep-Alive Service Setup Guide

**Status:** Action Required
**Updated:** January 6, 2026
**Backend HEAD Support:** ✅ Added (supports both GET and HEAD requests)

## Problem

The GitHub Actions workflow (`.github/workflows/keep-alive.yml`) exists but is **NOT reliable** for keeping the Render free tier backend alive because:

- GitHub Actions has unpredictable delays (3-10+ minutes during high load)
- Render spins down after exactly 15 minutes of inactivity
- Missing even one ping causes spin-down
- GitHub Actions cannot guarantee consistent timing

## Solution: Use UptimeRobot (Recommended)

UptimeRobot is a free, reliable monitoring service that will ping your backend every 5 minutes, keeping it awake 24/7.

### Why UptimeRobot?

✅ **Most reliable** - 99.9%+ uptime, industry standard
✅ **Bonus features** - Email alerts, uptime monitoring, incident history
✅ **Easiest setup** - 5 minutes, no code changes needed
✅ **Completely free** - Forever free tier with 50 monitors
✅ **Set and forget** - No maintenance required
✅ **HEAD support** - Backend supports HEAD requests (more efficient, works with free tiers)

---

## Step-by-Step Setup (5 minutes)

### Step 1: Create UptimeRobot Account

1. Go to: https://uptimerobot.com/signUp
2. Sign up with email or GitHub OAuth
3. Verify your email
4. Log in to the dashboard

### Step 2: Add Backend Monitor

1. Click **"Add New Monitor"** button (big green plus icon)
2. Fill in the following details:

```
Monitor Type: HTTP(s)
Friendly Name: MnM Dashboard Backend
URL (or IP): https://mnm-home.onrender.com/
Monitoring Interval: 5 minutes
Monitor Timeout: 30 seconds
HTTP Method: HEAD (more efficient) or GET (both supported)
```

3. Click **"Create Monitor"**
4. Monitor starts immediately! ✨

### Step 3: Verify It's Working (wait 5-10 minutes)

1. Wait 5-10 minutes for the first few pings
2. Check UptimeRobot dashboard for a green checkmark ✅
3. Click on your monitor to see ping history
4. Response time should be ~200-500ms

### Step 4: Optional - Configure Email Alerts

1. In monitor settings, go to **"Alert Contacts"**
2. Add your email address
3. Set alert threshold: **Down for 2 minutes**
4. Save

Now you'll get emailed if your backend ever goes down!

---

## Verification Tests

### Immediate Test (Right After Setup)

```bash
# Test backend responds correctly
curl -s https://mnm-home.onrender.com/ | jq

# Expected output:
# {
#   "message": "MnM Dashboard API",
#   "status": "running",
#   "version": "1.0.0"
# }
```

### 30-Minute Cold Start Test

1. **Don't access the dashboard for 30 minutes** (backend would normally spin down at 15 min)
2. Open: https://mnm-dashboard-frontend.onrender.com
3. **Expected:** Instant load (no 30-second cold start) ✨
4. Check UptimeRobot dashboard - should show 6+ successful pings

### 24-Hour Validation (Next Day)

1. Check UptimeRobot dashboard the next morning
2. **Expected results:**
   - Uptime: 100% or 99.9%+
   - Total pings: ~288 (24 hours × 12 pings/hour)
   - Response time: Consistent ~200-500ms
   - Zero downtime events

---

## Alternative: cron-job.org (More Precise Timing)

If you prefer 14-minute intervals instead of 5-minute:

### Setup

1. Go to: https://cron-job.org/en/signup/
2. Sign up and verify email
3. Click **"Create cronjob"**
4. Fill in:

```
Title: MnM Dashboard Keep-Alive
Address: https://mnm-home.onrender.com/
Request Method: HEAD (or GET - both supported)
Schedule: */14 * * * * (every 14 minutes)
Execution: Enabled
Save responses: Enabled (for debugging)
```

5. Save cron job
6. Wait 14 minutes and check execution history

---

## What to Do with GitHub Actions Workflow

The existing `.github/workflows/keep-alive.yml` can be:

**Option 1: Keep as backup** (recommended)
- Leave it in place as a fallback
- It won't hurt anything
- May help during UptimeRobot downtime (rare)

**Option 2: Delete it** (cleaner)
- Since UptimeRobot is more reliable
- Removes unnecessary code

**Option 3: Disable it**
- Comment out the `schedule:` section
- Keeps code for reference

---

## Success Checklist

After completing setup, you should have:

- ✅ UptimeRobot account created
- ✅ Monitor active and pinging every 5 minutes
- ✅ First 3-5 pings completed successfully
- ✅ 30-minute cold start test PASSED (instant load)
- ✅ Backend response time < 1 second
- ✅ (Optional) Email alerts configured
- ✅ Documentation updated (PROJECT_STATUS.md, CLAUDE.md, INITIAL.md)

---

## Troubleshooting

### UptimeRobot shows "Down" status

**Diagnosis:**
```bash
# Check if backend is actually down
curl -I https://mnm-home.onrender.com/
```

**Solutions:**
- If backend is down → Restart in Render dashboard
- If URL wrong → Edit monitor, fix URL, save
- If timeout too short → Increase to 60 seconds
- If SSL error → Verify URL is `https://` not `http://`

### Backend still spins down

**Check monitoring service:**
1. Verify pings are running every 5 minutes
2. Check for gaps > 15 minutes in execution history
3. Ensure monitor is enabled (not paused)

**Solutions:**
- If no pings → Reactivate monitor
- If gaps > 15 min → Service may have issues, try cron-job.org instead
- If many failures → Check backend health, may need restart

---

## Cost Analysis

**UptimeRobot:**
- Setup: $0.00
- Monthly: $0.00
- Forever free

**cron-job.org:**
- Setup: $0.00
- Monthly: $0.00
- Forever free

**Total cost: $0.00/month** ✨

---

## Next Steps

1. **Right now:** Set up UptimeRobot (5 minutes)
2. **In 30 minutes:** Run cold start test
3. **Tomorrow:** Check 24-hour validation
4. **Next week:** Verify long-term reliability (should be 99.9%+ uptime)

Once set up, it's completely hands-off! 🎉

---

## Documentation to Update After Setup

After you've verified UptimeRobot is working:

1. **PROJECT_STATUS.md** - Mark keep-alive as "✅ Working with UptimeRobot"
2. **CLAUDE.md** - Update "Keep-Alive Service" section
3. **INITIAL.md** - Remove the issue about keep-alive not working

---

**Need help?** Check the full PRP at `PRPs/fix-keep-alive-service.md`
