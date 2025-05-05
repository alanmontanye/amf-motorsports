-- SQLite script to add hour tracking columns to ATV table
-- Run with: sqlite3 app.db < db_alter.sql

-- Add columns if they don't exist
ALTER TABLE atv ADD COLUMN acquisition_hours FLOAT DEFAULT 0;
ALTER TABLE atv ADD COLUMN repair_hours FLOAT DEFAULT 0;
ALTER TABLE atv ADD COLUMN selling_hours FLOAT DEFAULT 0;
ALTER TABLE atv ADD COLUMN total_hours FLOAT DEFAULT 0;

-- Update default values for existing records
UPDATE atv SET 
  acquisition_hours = 0 WHERE acquisition_hours IS NULL;

UPDATE atv SET 
  repair_hours = 0 WHERE repair_hours IS NULL;

UPDATE atv SET 
  selling_hours = 0 WHERE selling_hours IS NULL;

UPDATE atv SET 
  total_hours = 0 WHERE total_hours IS NULL;

-- Calculate total hours based on individual hour types
UPDATE atv SET 
  total_hours = COALESCE(acquisition_hours, 0) + COALESCE(repair_hours, 0) + COALESCE(selling_hours, 0);

-- Verify the columns were added
PRAGMA table_info(atv);
