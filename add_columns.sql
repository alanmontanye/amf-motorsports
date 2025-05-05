-- Add hours tracking columns
ALTER TABLE atv ADD COLUMN acquisition_hours FLOAT DEFAULT 0;
ALTER TABLE atv ADD COLUMN repair_hours FLOAT DEFAULT 0;
ALTER TABLE atv ADD COLUMN selling_hours FLOAT DEFAULT 0;
ALTER TABLE atv ADD COLUMN total_hours FLOAT DEFAULT 0;
