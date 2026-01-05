# Deployment Validation Checklist

Use this checklist to verify your production deployment is working correctly.

---

## Pre-Deployment Validation

### Local Environment
- [ ] Frontend builds successfully: `cd frontend && npm run build`
- [ ] Backend runs locally: `cd backend && uvicorn app.main:app --reload`
- [ ] Database connection works: `python backend/init_db.py` (creates tables)
- [ ] All .env files are in .gitignore
- [ ] No sensitive data committed to git: `git status` shows no .env files

### Repository Setup
- [ ] Code pushed to GitHub main branch
- [ ] backend/.env removed from git tracking (if previously added)
- [ ] backend/.gitignore exists and includes .env
- [ ] frontend/.gitignore includes *.local

---

## Render Backend Deployment

### Configuration
- [ ] Root Directory set to: `backend`
- [ ] Build Command: `pip install -r requirements.txt`
- [ ] Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] Instance Type: Free
- [ ] Environment variable `DATABASE_URL` configured with Neon connection string
- [ ] Connection string uses `postgresql+asyncpg://` scheme
- [ ] Connection string includes `?sslmode=require`

### Deployment Status
- [ ] Build completed successfully (check logs)
- [ ] Service shows "Live" status
- [ ] No errors in deployment logs
- [ ] Backend URL recorded: `https://_____.onrender.com`

### Backend Health Checks
- [ ] Root endpoint works: `https://your-backend.onrender.com/`
  - Expected response: `{"message": "MnM Dashboard API", "status": "running", "version": "1.0.0"}`
- [ ] API docs accessible: `https://your-backend.onrender.com/docs`
  - Shows FastAPI Swagger UI
- [ ] Session review endpoint: `GET https://your-backend.onrender.com/api/session-review`
  - Returns 200 status
  - Returns session review data
- [ ] Pick stats endpoint: `GET https://your-backend.onrender.com/api/pick-stats`
  - Returns 200 status
  - Returns array of pick stats

---

## Vercel Frontend Deployment

### Configuration
- [ ] Framework Preset: Vite (auto-detected)
- [ ] Root Directory: `frontend`
- [ ] Build Command: `npm run build`
- [ ] Output Directory: `dist`
- [ ] Environment variable `VITE_API_URL` set to Render backend URL (no trailing slash)
- [ ] Environment variable applied to all environments (Production, Preview, Development)

### Deployment Status
- [ ] Build completed successfully (check logs)
- [ ] Deployment shows "Ready" status
- [ ] No build errors in logs
- [ ] Frontend URL recorded: `https://_____.vercel.app`

### Frontend Health Checks
- [ ] App loads without errors
- [ ] Browser console shows no errors (F12 > Console)
- [ ] No CORS errors in console
- [ ] Network tab shows API calls hitting Render backend
- [ ] All API calls return 200 status codes

---

## CORS Security Configuration

### Backend CORS Update
- [ ] Vercel domain added to `backend/app/main.py` allow_origins
- [ ] Exact domain used (no wildcards like `*.vercel.app`)
- [ ] Localhost origins preserved for local development
- [ ] Changes committed to git
- [ ] Changes pushed to GitHub: `git push origin main`
- [ ] Render auto-deployment triggered
- [ ] Render redeployment completed successfully

### CORS Verification
- [ ] Open Vercel URL in browser
- [ ] Open DevTools (F12) > Console
- [ ] No CORS errors appear
- [ ] Network tab shows successful API calls (200 status)
- [ ] All requests to Render backend succeed

---

## End-to-End Feature Testing

### 1. Session Review
- [ ] Component loads and displays current notes
- [ ] Can edit notes in textarea
- [ ] Click "Save Changes" button
- [ ] Success message appears
- [ ] Refresh page (F5)
- [ ] **Verify:** Notes persist after refresh

### 2. Weekly Champions
- [ ] Component loads with current week
- [ ] Player/champion grid displays correctly
- [ ] Can toggle checkboxes
- [ ] Checkboxes change state immediately
- [ ] Refresh page (F5)
- [ ] **Verify:** Checkbox states persist after refresh
- [ ] Week selector works (if implemented)

### 3. Draft Notes
- [ ] Component loads and displays current notes
- [ ] Can edit notes in textarea
- [ ] Click "Save Changes" button
- [ ] Success message appears
- [ ] Refresh page (F5)
- [ ] **Verify:** Notes persist after refresh

### 4. Pick Stats
- [ ] Component loads with existing pick stats
- [ ] Table displays champion names, games, wins, losses, win rate
- [ ] Can add new champion via input field
- [ ] New champion appears in table with 0 games
- [ ] Click "Win" button on a champion
- [ ] **Verify:** Wins increment, games increment, win rate updates
- [ ] Click "Loss" button on a champion
- [ ] **Verify:** Losses increment, games increment, win rate updates
- [ ] Refresh page (F5)
- [ ] **Verify:** All stats persist after refresh
- [ ] Delete a champion (if delete is implemented)
- [ ] **Verify:** Champion removed from list

---

## Mobile Responsiveness Testing

### Desktop View (1920x1080)
- [ ] Dashboard layout displays correctly
- [ ] All four sections visible
- [ ] No horizontal scrolling
- [ ] No layout overflow

### Tablet View (768x1024)
- [ ] Layout adapts to smaller screen
- [ ] Sections stack or resize appropriately
- [ ] All features remain functional
- [ ] Touch interactions work

### Mobile View (375x667)
- [ ] App is usable on mobile
- [ ] Text is readable without zooming
- [ ] Buttons are tappable
- [ ] Forms are usable
- [ ] No horizontal scrolling

### Real Device Test (Optional)
- [ ] Open Vercel URL on actual phone
- [ ] Perform one CRUD operation (e.g., save session notes)
- [ ] **Verify:** Changes persist and sync

---

## Multi-User Testing (Optional)

- [ ] Share Vercel URL with 2+ teammates
- [ ] User A makes a change (e.g., adds champion stat)
- [ ] User B refreshes their browser
- [ ] **Verify:** User B sees User A's change
- [ ] Both users make simultaneous changes
- [ ] Both refresh
- [ ] **Verify:** Data syncs correctly without conflicts

---

## Auto-Deployment Verification

### Render Auto-Deploy
- [ ] Make a small change to backend code (e.g., update version in main.py)
- [ ] Commit and push to main: `git push origin main`
- [ ] Check Render dashboard for new deployment
- [ ] **Verify:** Deployment triggers automatically
- [ ] **Verify:** Deployment completes successfully
- [ ] **Verify:** Change is live in production

### Vercel Auto-Deploy
- [ ] Make a small change to frontend code (e.g., update a label)
- [ ] Commit and push to main: `git push origin main`
- [ ] Check Vercel dashboard for new deployment
- [ ] **Verify:** Deployment triggers automatically
- [ ] **Verify:** Build completes successfully
- [ ] **Verify:** Change is live in production

---

## Performance Testing

### Cold Start (Render Free Tier)
- [ ] Wait 15+ minutes without accessing backend
- [ ] Make first request to Vercel app
- [ ] **Expected:** ~60 second delay on first load
- [ ] **Verify:** Subsequent requests are fast
- [ ] **Note:** If cold starts are unacceptable, implement keep-alive service

### Page Load Speed
- [ ] Open Vercel URL in Incognito/Private mode
- [ ] Use browser DevTools > Network tab
- [ ] Record page load time
- [ ] **Target:** Initial load under 3 seconds
- [ ] **Verify:** Acceptable performance for users

### API Response Times
- [ ] Check Network tab for API call durations
- [ ] Session review GET: ____ ms
- [ ] Pick stats GET: ____ ms
- [ ] Session review PUT: ____ ms
- [ ] Pick stats POST: ____ ms
- [ ] **Target:** Under 500ms for most requests (after warm-up)

---

## Security Verification

### HTTPS Enforcement
- [ ] Try accessing frontend with `http://` (should redirect to `https://`)
- [ ] Try accessing backend with `http://` (should redirect to `https://`)
- [ ] **Verify:** Both platforms enforce HTTPS

### CORS Protection
- [ ] Open browser console on a different domain (e.g., google.com)
- [ ] Try to fetch from your Render API:
  ```javascript
  fetch('https://your-backend.onrender.com/api/session-review')
  ```
- [ ] **Verify:** CORS error appears (blocked)
- [ ] Open console on your Vercel domain
- [ ] Same fetch should succeed
- [ ] **Verify:** CORS allows only whitelisted domains

### Environment Variables
- [ ] Check Render dashboard > Environment
- [ ] **Verify:** DATABASE_URL is not visible in build logs
- [ ] Check Vercel dashboard > Settings > Environment Variables
- [ ] **Verify:** VITE_API_URL is set correctly
- [ ] **Verify:** No sensitive data exposed in frontend bundle

---

## Database Persistence

### Data Integrity
- [ ] Add several test records (champions, notes, etc.)
- [ ] Close all browser windows
- [ ] Clear browser cache
- [ ] Wait 5 minutes
- [ ] Open Vercel URL again
- [ ] **Verify:** All data is still present
- [ ] **Verify:** No data loss occurred

### Concurrent Writes (Optional)
- [ ] Two users add different champions simultaneously
- [ ] Both refresh
- [ ] **Verify:** Both champions appear in list
- [ ] **Verify:** No data corruption or loss

---

## Free Tier Monitoring

### Render
- [ ] Check Render dashboard > Usage
- [ ] Note current instance hours used
- [ ] **Verify:** Under 750 hours/month limit
- [ ] Note bandwidth usage
- [ ] **Verify:** Within free tier limits

### Vercel
- [ ] Check Vercel dashboard > Usage
- [ ] Note build minutes used
- [ ] **Verify:** Under 6000 minutes/month limit
- [ ] Note bandwidth usage
- [ ] **Verify:** Under 100 GB/month limit

### Neon
- [ ] Check Neon dashboard > Usage
- [ ] Note storage used
- [ ] **Verify:** Under 3 GB limit
- [ ] Note compute hours
- [ ] **Verify:** Under ~192 hours/month limit

---

## Documentation Updates

### PROJECT_STATUS.md
- [ ] Add production backend URL
- [ ] Add production frontend URL
- [ ] Update deployment status to "Completed"
- [ ] Note any deployment issues encountered
- [ ] Add deployment date

### Team Communication
- [ ] Share production URL with team
- [ ] Document any known issues or limitations
- [ ] Provide access instructions if needed
- [ ] Share deployment credentials (if applicable)

---

## Optional Enhancements

### Keep-Alive Service (UptimeRobot)
- [ ] Sign up for UptimeRobot free account
- [ ] Create HTTP monitor for Render backend
- [ ] Set check interval to 5 minutes
- [ ] Monitor URL: `https://your-backend.onrender.com/`
- [ ] **Verify:** Backend stays warm (no cold starts)

### Custom Domain (Vercel)
- [ ] Purchase custom domain (if desired)
- [ ] Add domain in Vercel dashboard
- [ ] Configure DNS records
- [ ] Wait for SSL certificate
- [ ] Update CORS in backend with new domain
- [ ] Test custom domain

### Branch Previews (Vercel)
- [ ] Create feature branch: `git checkout -b test-feature`
- [ ] Push to GitHub: `git push origin test-feature`
- [ ] Check Vercel dashboard for preview deployment
- [ ] **Verify:** Preview URL created automatically
- [ ] **Verify:** Preview doesn't affect production

---

## Rollback Plan

### If Deployment Fails
- [ ] Document the error from logs
- [ ] Check environment variables are correct
- [ ] Verify build/start commands
- [ ] Check root directory settings
- [ ] Review Troubleshooting section in DEPLOYMENT.md

### If Production Has Issues
- [ ] Identify the problem (frontend, backend, database, CORS)
- [ ] Check recent commits: `git log`
- [ ] If needed, revert to previous version: `git revert <commit-hash>`
- [ ] Push revert to trigger redeployment
- [ ] Verify issue is resolved

---

## Final Sign-Off

### Deployment Complete When:
- [ ] All backend health checks pass
- [ ] All frontend health checks pass
- [ ] All four dashboard features work end-to-end
- [ ] Data persists after browser refresh
- [ ] No CORS errors in console
- [ ] Auto-deployments configured on both platforms
- [ ] Production URLs documented
- [ ] Team has access to production app
- [ ] Free tier usage is within limits

**Deployment Date:** _______________

**Deployed By:** _______________

**Production URLs:**
- Frontend: _______________
- Backend: _______________
- API Docs: _______________/docs

**Notes/Issues:**
_______________________________________________
_______________________________________________

---

**Status:** Ready for use!
