import { createClient } from '@supabase/supabase-js';

export const supabase = createClient(
  'https://wnczsazerzoqbmkjrgfp.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InduY3pzYXplcnpvcWJta2pyZ2ZwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDYyMTE5ODUsImV4cCI6MjA2MTc4Nzk4NX0.voaSF0KRcTRkyVgDExpdWbBOmRauiylMxsvPE0BUuEk'
);
