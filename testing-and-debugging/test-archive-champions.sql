-- ========================================
-- TEST ARCHIVE: Archive all champion pool entries
-- ========================================
-- This script backs up and deletes all champion_pools entries
-- so you can test the accountability check with no champion data.
-- Run test-restore-champions.sql to undo this.
-- ========================================

-- Create backup table if it doesn't exist
CREATE TABLE IF NOT EXISTS champion_pools_test_backup (
    id integer,
    player_name character varying,
    champion_name character varying,
    description text,
    pick_priority text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    backed_up_at timestamp with time zone DEFAULT now()
);

-- Clear any previous test backup
DELETE FROM champion_pools_test_backup;

-- Back up all current champion pool entries
INSERT INTO champion_pools_test_backup (
    id, player_name, champion_name, description, pick_priority, created_at, updated_at
)
SELECT
    id, player_name, champion_name, description, pick_priority, created_at, updated_at
FROM champion_pools;

-- Delete all champion pool entries (THIS WILL MAKE ACCOUNTABILITY CHECK SHOW 0 GAMES FOR ALL PLAYERS)
DELETE FROM champion_pools;

-- Verify the archive
SELECT
    COUNT(*) as backed_up_count,
    MIN(backed_up_at) as backup_time
FROM champion_pools_test_backup;

SELECT
    COUNT(*) as remaining_count
FROM champion_pools;
