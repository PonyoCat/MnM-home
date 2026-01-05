# GitHub Actions Workflows

This directory contains automated workflows for the MnM Dashboard project.

## Workflows

### keep-alive.yml

**Purpose:** Prevent Render free tier backend from spinning down after 15 minutes of inactivity.

**What it does:**
- Automatically pings the backend at `https://mnm-home.onrender.com/` every 14 minutes
- Keeps the backend "awake" 24/7
- Eliminates 30-second cold starts for users
- Provides instant page loads

**Schedule:**
- Runs every 14 minutes via cron: `*/14 * * * *`
- Can be manually triggered from GitHub Actions UI

**Cost:** $0 (Free for all repositories)

**Monitoring:**
- Go to repository > Actions > "Keep Backend Alive"
- View execution history and logs
- Check for failed pings (should be < 1% failure rate)

**Documentation:**
- [KEEP_ALIVE_SETUP.md](../KEEP_ALIVE_SETUP.md) - Setup guide
- [KEEP_ALIVE_VALIDATION.md](../KEEP_ALIVE_VALIDATION.md) - Validation checklist
- [PRPs/keep-alive-service.md](../PRPs/keep-alive-service.md) - Original requirement

## Troubleshooting

### Workflow Not Running

If scheduled runs are not appearing:
1. Verify GitHub Actions are enabled (Settings > Actions)
2. Check if repository is public (required for free tier scheduled workflows)
3. Validate workflow file syntax (`.github/workflows/keep-alive.yml`)
4. Ensure "Allow all actions" is enabled in repository settings

### Manual Trigger

To manually test the workflow:
1. Go to Actions tab
2. Click "Keep Backend Alive"
3. Click "Run workflow" dropdown
4. Select "main" branch
5. Click "Run workflow" button
6. Wait 10-20 seconds and refresh
7. Click on the run to view logs

### Expected Output

Successful run should show:
```
Pinging backend to prevent Render spin-down...
Target: https://mnm-home.onrender.com/
Time: [timestamp]
✅ Backend is alive! (HTTP 200)
Keep-alive ping completed successfully at [timestamp]
```

## Adding More Workflows

To add additional workflows:
1. Create a new `.yml` file in this directory
2. Define the workflow triggers and jobs
3. Commit and push to GitHub
4. Workflow will appear in Actions tab

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [Cron Syntax](https://docs.github.com/en/actions/reference/events-that-trigger-workflows#scheduled-events)
