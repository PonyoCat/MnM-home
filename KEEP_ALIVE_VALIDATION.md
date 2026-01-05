# Keep-Alive Service Validation

**Purpose:** Verify the keep-alive service is working correctly

**Date:** January 5, 2026

---

## Pre-Activation Validation

### ✅ Backend Accessibility

Test the backend is live and responding:

```bash
curl https://mnm-home.onrender.com/
```

**Expected Response:**
```json
{"message":"MnM Dashboard API","status":"running","version":"1.0.0"}
```

**Status:** ✅ VERIFIED (HTTP 200 OK)

---

## Activation Steps

### Step 1: Push GitHub Actions Workflow

The workflow file has been created at `.github/workflows/keep-alive.yml`

To activate:

```bash
git add .github/workflows/keep-alive.yml
git commit -m "Add keep-alive GitHub Action to prevent Render spin-down"
git push origin main
```

### Step 2: Enable GitHub Actions (if needed)

If this is your first GitHub Action:

1. Go to your GitHub repository
2. Click on "Actions" tab
3. If prompted, click "I understand my workflows, go ahead and enable them"

### Step 3: Verify Workflow is Enabled

1. Go to GitHub repository > Actions tab
2. Look for "Keep Backend Alive" workflow in the left sidebar
3. Click on it
4. You should see:
   - Workflow enabled (toggle should be green)
   - Scheduled runs listed (may take up to 14 minutes for first run)

---

## Post-Activation Validation

### Immediate Checks (After Push)

**1. Workflow File in Repository**
- [ ] Navigate to `.github/workflows/keep-alive.yml` on GitHub
- [ ] Verify file is present and correctly formatted

**2. Actions Tab**
- [ ] Go to repository > Actions
- [ ] Verify "Keep Backend Alive" workflow appears
- [ ] Check if workflow is enabled (should be green)

**3. Manual Trigger Test**
- [ ] Go to Actions > Keep Backend Alive
- [ ] Click "Run workflow" dropdown
- [ ] Select "main" branch
- [ ] Click green "Run workflow" button
- [ ] Wait 10-20 seconds
- [ ] Refresh page
- [ ] Verify workflow run appears with status (should complete in ~5 seconds)
- [ ] Click on the run to view logs
- [ ] Verify output shows "✅ Backend is alive! (HTTP 200)"

---

## Scheduled Run Validation (14 Minutes After Push)

### Check First Scheduled Run

Wait at least 14 minutes after push, then:

**1. View Workflow Runs**
- [ ] Go to Actions > Keep Backend Alive
- [ ] Look for automatically triggered runs (icon shows a clock)
- [ ] Verify at least one scheduled run has completed

**2. Inspect Logs**
- [ ] Click on a scheduled run
- [ ] Click on "keep-alive" job
- [ ] Expand "Ping Backend Health Check" step
- [ ] Verify output contains:
  ```
  Pinging backend to prevent Render spin-down...
  Target: https://mnm-home.onrender.com/
  Time: [timestamp]
  ✅ Backend is alive! (HTTP 200)
  ```

**3. Verify Schedule**
- [ ] Note the timestamp of the first run
- [ ] Wait for second run (should be 14 minutes later)
- [ ] Verify second run occurred at expected time
- [ ] Confirm runs are happening every 14 minutes

---

## Long-Term Validation (24 Hours)

### Cold Start Test

**Purpose:** Verify backend never spins down with keep-alive active

**Steps:**
1. Wait 20+ minutes without manually accessing the backend
2. Open frontend: https://mnm-dashboard-frontend.onrender.com
3. Observe page load time

**Expected Results:**
- [ ] Page loads instantly (< 2 seconds)
- [ ] No 30-second "cold start" delay
- [ ] All API calls return immediately
- [ ] No "service starting" messages

**If cold start occurs:**
- Check GitHub Actions runs for the past 20 minutes
- Verify keep-alive pings succeeded (HTTP 200)
- Check Render logs for unexpected restarts

---

## Monitoring

### GitHub Actions Run History

View execution history:
1. Go to Actions > Keep Backend Alive
2. Review recent runs
3. Look for any failures (red X icons)

**Success Criteria:**
- [ ] 95%+ success rate
- [ ] No more than 1-2 failures per week
- [ ] Failures are transient (retry succeeds)

### Render Service Status

Check backend uptime:
1. Go to Render Dashboard
2. Select mnm-home service
3. View "Events" tab
4. Check for "Service is live" events

**Expected Behavior:**
- Service stays in "live" state continuously
- No "Service is sleeping" events
- No frequent restarts

---

## Troubleshooting

### Workflow Not Running

**Symptoms:**
- No runs appear in Actions tab after 14+ minutes
- Workflow shows as "disabled"

**Solutions:**
1. Verify GitHub Actions are enabled for the repository
2. Check if repository is public (required for free tier scheduled workflows)
3. Verify workflow file syntax is correct (YAML validation)
4. Check repository settings > Actions > General > "Allow all actions"

### Pings Failing (HTTP != 200)

**Symptoms:**
- Workflow runs show failures
- Logs show "⚠️ Unexpected response" or "❌ Keep-alive ping failed"

**Solutions:**
1. Test backend manually: `curl https://mnm-home.onrender.com/`
2. Check Render dashboard for deployment errors
3. Verify DATABASE_URL is set correctly on Render
4. Check Render logs for backend crashes

### Backend Still Spinning Down

**Symptoms:**
- First request after inactivity takes 30+ seconds
- Render shows "Service is sleeping" events

**Possible Causes:**
- Workflow runs less frequently than every 15 minutes
- Pings are failing silently
- Render service is on a different sleep threshold

**Solutions:**
1. Verify workflow runs every 14 minutes (check Actions history)
2. Reduce cron interval to `*/10 * * * *` (every 10 minutes)
3. Check Render service logs for sleep events
4. Consider using UptimeRobot as backup (5-minute interval)

---

## Alternative: Add UptimeRobot as Backup

For redundancy, you can add UptimeRobot alongside GitHub Actions:

**Setup (5 minutes):**
1. Go to https://uptimerobot.com/signUp
2. Create free account
3. Add new monitor:
   - Type: HTTP(s)
   - URL: https://mnm-home.onrender.com/
   - Interval: 5 minutes
4. Save

**Benefits:**
- Dual monitoring (GitHub Actions + UptimeRobot)
- Email alerts if backend goes down
- More frequent pings (5 min vs 14 min)
- Independent of GitHub Actions status

---

## Success Metrics

After 7 days of operation:

**GitHub Actions:**
- [ ] 500+ successful runs (one every 14 minutes)
- [ ] < 1% failure rate
- [ ] Consistent 14-minute intervals

**Backend Performance:**
- [ ] Zero cold starts experienced by users
- [ ] Instant page loads (< 2 seconds)
- [ ] 99.9%+ uptime on Render dashboard

**User Experience:**
- [ ] No complaints about slow loading
- [ ] Seamless access to dashboard
- [ ] No "service starting" delays

---

## Validation Checklist Summary

### Immediate (0-30 minutes)
- [x] Backend is accessible (HTTP 200)
- [ ] Workflow file pushed to GitHub
- [ ] Workflow appears in Actions tab
- [ ] Manual workflow run succeeds

### Short-term (1-24 hours)
- [ ] First scheduled run completes successfully
- [ ] Runs occur every 14 minutes
- [ ] No cold starts experienced
- [ ] Backend stays "live" on Render

### Long-term (7+ days)
- [ ] Consistent scheduled runs
- [ ] < 1% failure rate
- [ ] Zero user-facing cold starts
- [ ] Backend uptime > 99.9%

---

## Completion

When all validation steps pass:

- [ ] Update [PROJECT_STATUS.md](PROJECT_STATUS.md) with keep-alive completion
- [ ] Mark keep-alive item as complete in deployment checklist
- [ ] Move [PRPs/keep-alive-service.md](PRPs/keep-alive-service.md) to `PRPs/implemented/`
- [ ] Document actual uptime metrics after 7 days

**Status:** Ready to validate after workflow is pushed to GitHub!
