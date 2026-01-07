# Test Archive System

Quick scripts to archive and restore champion pool data for testing the accountability check.

## What This Does

The **accountability check** relies on the `champion_pools` table to know which champions each player should be playing. When you archive all champions, the accountability check will show **0 games played** for all players, even if they have weekly champion data.

## Current Data

- **Sinus:** 5 champions
- **Elias:** 5 champions

## Quick Start

### Archive (Delete) All Champions

```powershell
.\test-archive.ps1
```

This will:
1. Back up all champion pool entries to `champion_pools_test_backup` table
2. Delete all entries from `champion_pools`
3. Let you test the accountability check with no champion data

### Restore All Champions

```powershell
.\test-restore.ps1
```

This will:
1. Restore all champion pool entries from the backup
2. Delete the backup table
3. Return everything to normal

## Manual SQL Usage

If you prefer to run SQL directly:

### Archive
```bash
psql -h <host> -U <user> -d <db> -f test-archive-champions.sql
```

### Restore
```bash
psql -h <host> -U <user> -d <db> -f test-restore-champions.sql
```

## Testing the Accountability Check

After running the archive:

1. Visit: https://mnm-dashboard-frontend.onrender.com/
2. Look at the **Accountability Check** section
3. You should see all players listed with **0 games played** on their pool champions
4. This tests the behavior when players haven't set up their champion pools yet

## Safety

- The backup is stored in a temporary table: `champion_pools_test_backup`
- The restore script will return everything to exactly how it was
- If something goes wrong, the backup data is still in the database

## Cleanup

After you're done testing, run:
```powershell
.\test-restore.ps1
```

The restore script will automatically clean up the backup table.
