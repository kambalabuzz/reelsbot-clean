-- Check the pending job status
SELECT 
  id,
  video_id,
  status,
  priority,
  attempts,
  locked_by,
  locked_at,
  next_run_at,
  NOW() as current_time,
  (next_run_at IS NULL OR next_run_at <= NOW()) as can_run_now
FROM assembly_jobs
WHERE video_id = '5be25394'
ORDER BY created_at DESC
LIMIT 3;

-- Fix the job to run immediately
UPDATE assembly_jobs
SET 
  next_run_at = NOW() - INTERVAL '1 second',
  status = 'pending'
WHERE video_id = '5be25394'
  AND status = 'pending';

-- Verify
SELECT 
  id,
  video_id,
  status,
  next_run_at,
  NOW() as current_time
FROM assembly_jobs
WHERE video_id = '5be25394'
ORDER BY created_at DESC
LIMIT 1;
