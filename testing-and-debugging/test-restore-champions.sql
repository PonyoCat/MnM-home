-- ========================================
-- TEST RESTORE: Restore all champion pool entries
-- ========================================
-- This script restores all champion_pools entries
-- from the test backup created by test-archive-champions.sql
-- ========================================

-- Restore all champion pool entries from backup
INSERT INTO champion_pools (
    id, player_name, champion_name, description, pick_priority, created_at, updated_at
)
SELECT
    id, player_name, champion_name, description, pick_priority, created_at, updated_at
FROM champion_pools_test_backup;

-- Update the sequence to prevent ID conflicts
SELECT setval('champion_pools_id_seq', COALESCE((SELECT MAX(id) FROM champion_pools), 1));

-- Clean up the backup table
DROP TABLE IF EXISTS champion_pools_test_backup;

-- Verify the restore
SELECT
    COUNT(*) as restored_count,
    COUNT(DISTINCT player_name) as player_count
FROM champion_pools;
