-- Migration: Add challenge_type and custom_variables to challenges table
-- Date: 2025-12-29
-- Description: Adds fields to support Simple vs Advanced challenge types with custom variables

-- Add challenge_type column (default to "simple")
ALTER TABLE challenges ADD COLUMN challenge_type VARCHAR(20) DEFAULT 'simple';

-- Add custom_variables column (JSON for variable substitution)
ALTER TABLE challenges ADD COLUMN custom_variables TEXT DEFAULT '{}';

-- Auto-classify existing challenges as "advanced" if they have steps
UPDATE challenges
SET challenge_type = 'advanced'
WHERE id IN (
  SELECT DISTINCT challenge_id FROM challenge_steps
);

-- All other challenges remain "simple" (default)

-- Create index on challenge_type for filtering performance
CREATE INDEX idx_challenges_challenge_type ON challenges(challenge_type);
