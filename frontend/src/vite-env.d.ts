/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_BACKEND_URL: string
  readonly VITE_SUPABASE_URL: string
  readonly VITE_SUPABASE_ANON_KEY: string
  // Add other env variables you might use in frontend
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
