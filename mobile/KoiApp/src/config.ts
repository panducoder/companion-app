// App configuration
// Values come from EXPO_PUBLIC_ environment variables at build time.
// For local development, create a .env file in the KoiApp root with:
//   EXPO_PUBLIC_SUPABASE_URL=https://vkybqfcadvgiuhrkugrb.supabase.co
//   EXPO_PUBLIC_SUPABASE_ANON_KEY=<your-anon-key>
//   EXPO_PUBLIC_LIVEKIT_URL=wss://koi-ve3if36d.livekit.cloud

export const config = {
  supabase: {
    url: process.env.EXPO_PUBLIC_SUPABASE_URL ?? 'https://vkybqfcadvgiuhrkugrb.supabase.co',
    anonKey:
      process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY ??
      'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreWJxZmNhZHZnaXVocmt1Z3JiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA3MzY2NzUsImV4cCI6MjA4NjMxMjY3NX0.cTokXeP4r2FMMRrIvsQaTFbqANQidk5salVePdSR28w',
  },
  livekit: {
    url: process.env.EXPO_PUBLIC_LIVEKIT_URL ?? 'wss://koi-ve3if36d.livekit.cloud',
  },
} as const;
