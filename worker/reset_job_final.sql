-- Reset the job back to pending with the video_id fix deployed
UPDATE assembly_jobs
SET 
  status = 'pending',
  attempts = 0,
  locked_by = NULL,
  locked_at = NULL,
  next_run_at = NOW(),
  last_error = NULL,
  updated_at = NOW()
WHERE id = '44d16e03-f900-40fb-a010-bd06dcbe6f41';

-- Verify
SELECT 
  id,
  video_id,
  status,
  attempts,
  locked_by,
  next_run_at
FROM assembly_jobs
WHERE id = '44d16e03-f900-40fb-a010-bd06dcbe6f41';
