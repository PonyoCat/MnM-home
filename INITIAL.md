## FEATURES

~~The keep alive system does not work on my backend (URL: https://mnm-home.onrender.com/)~~
~~After 15 minutes it shut down. But my frontend was still up.~~

**STATUS: FIXED** (January 6, 2026)
- **Issue:** GitHub Actions keep-alive workflow is unreliable (delays of 3-10+ minutes)
- **Root Cause:** GitHub Actions cannot guarantee consistent timing needed for Render's 15-minute deadline
- **Solution:** Use external monitoring service (UptimeRobot or cron-job.org)
- **Setup Guide:** See [KEEP_ALIVE_SETUP_GUIDE.md](KEEP_ALIVE_SETUP_GUIDE.md) for step-by-step instructions
- **Action Required:** User needs to set up UptimeRobot account (5 minutes, free forever)

## EXAMPLES:

[Provide and explain examples that you have in the `examples/` folder]

## DOCUMENTATION:

[List out any documentation (web pages, sources for an MCP server like Crawl4AI RAG, etc.) that will need to be referenced during development]

## OTHER CONSIDERATIONS:

[Any other considerations or specific requirements - great place to include gotchas that you see AI coding assistants miss with your projects a lot]