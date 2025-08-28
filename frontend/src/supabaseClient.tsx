import { createClient } from '@supabase/supabase-js';

export const supabase = createClient(
  'https://weohjgxhmlfhryzofkcg.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indlb2hqZ3hobWxmaHJ5em9ma2NnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTU1NTAxNzIsImV4cCI6MjA3MTEyNjE3Mn0.lR8--YwVz3dC3jnZik4OSRlVp7voURUwoNO4RI86j70'
);
