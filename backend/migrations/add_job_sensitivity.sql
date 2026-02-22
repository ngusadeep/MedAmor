-- Add sensitivity column to jobs table (optional per-job override for audit sensitivity)
-- Run manually if you have an existing database: psql $DATABASE_URL -f add_job_sensitivity.sql

ALTER TABLE jobs ADD COLUMN IF NOT EXISTS sensitivity DOUBLE PRECISION;
