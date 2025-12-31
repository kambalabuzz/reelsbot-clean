-- Force PostgREST to reload the schema
NOTIFY pgrst, 'reload schema';
NOTIFY pgrst, 'reload config';

-- Check the function exists and its signature
SELECT
  p.proname,
  pg_get_function_identity_arguments(p.oid) as signature,
  pg_get_functiondef(p.oid) as definition
FROM pg_proc p
WHERE p.proname = 'claim_assembly_job';
