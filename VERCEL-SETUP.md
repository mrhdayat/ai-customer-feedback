# Setup Vercel Deployment

## 🚀 Quick Fix untuk Error Build

### Masalah yang Teridentifikasi:
1. ❌ Vercel mencoba run root project (monorepo detection)
2. ❌ Build command salah
3. ✅ Railway backend sudah jalan di `http://localhost:4173/`

### Solusi:

## 1. Settings di Vercel Dashboard

Kunjungi Vercel Dashboard > Project Settings:

### Framework Preset:
- ✅ **Vite** (bukan "Other")

### Build & Output Settings:
- **Root Directory**: `frontend`
- **Build Command**: `npm run build` 
- **Output Directory**: `dist`
- **Install Command**: `npm install`

### Environment Variables:
Tambahkan di Vercel Dashboard > Environment Variables:

```bash
# Connect ke Railway Backend
VITE_BACKEND_URL=https://ai-customer-backend-production-xxxx.up.railway.app

# Disable demo mode karena ada backend
VITE_DEMO_MODE=false

# Supabase untuk direct access
VITE_SUPABASE_URL=https://dkxiszylxbgtenfsmzdk.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRreGlzenlseGJndGVuZnNtemRrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTUzNjE4MjQsImV4cCI6MjA3MDkzNzgyNH0.40_PFjb_rIdEUbbJPKnG6OX3N3cm6k5UWEwSnkmQQbc
```

## 2. Dapatkan Railway Backend URL

Di Railway Dashboard:
1. Klik project backend Anda
2. Klik tab "Settings" 
3. Copy "Public Domain" URL
4. Ganti `VITE_BACKEND_URL` di Vercel dengan URL ini

## 3. Test Full Stack

Setelah redeploy:
1. Frontend di Vercel akan connect ke Railway backend
2. Login `demo@cfd.app` / `demo12345` akan hit real backend
3. Real AI analysis akan berjalan

## 🔧 Alternative: Demo Mode Only

Jika ingin tetap demo mode (tanpa backend):

### Environment Variables di Vercel:
```bash
# Kosongkan atau hapus VITE_BACKEND_URL
# VITE_BACKEND_URL=

# Enable demo mode
VITE_DEMO_MODE=true
```

Demo mode akan aktif otomatis dan menggunakan mock data.

---

## 🎯 Rekomendasi

**Untuk showcase/demo**: Gunakan demo mode (lebih cepat, tidak perlu setup backend)

**Untuk production**: Connect ke Railway backend untuk real AI features
