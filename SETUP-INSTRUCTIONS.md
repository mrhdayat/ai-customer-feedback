# Panduan Setup Customer Feedback Dashboard

## 📋 Prasyarat

Pastikan Anda memiliki:
- Docker & Docker Compose terinstall
- Akun GitHub
- Akun Supabase (gratis)
- API Keys untuk AI services (opsional tapi direkomendasikan)

## 🚀 Setup Langkah demi Langkah

### 1. Clone Repository

```bash
git clone https://github.com/mrhdayat/ai-customer-feedback.git
cd ai-customer-feedback
```

### 2. Setup Environment Variables

```bash
# Copy template environment
cp env.example .env

# Edit file .env dengan API keys Anda
nano .env  # atau gunakan editor favorit Anda
```

**Environment Variables yang Diperlukan:**

```bash
# WAJIB - Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# OPSIONAL - AI Services (untuk fitur lengkap)
HUGGINGFACE_API_TOKEN=your-hf-token
REPLICATE_API_TOKEN=your-replicate-token
IBM_WATSON_NLU_API_KEY=your-watson-api-key
IBM_ORCHESTRATE_API_KEY=your-orchestrate-api-key
```

### 3. Setup Database Supabase

#### A. Buat Project Supabase
1. Kunjungi [https://supabase.io](https://supabase.io)
2. Buat akun dan project baru
3. Copy URL dan API keys ke file `.env`

#### B. Jalankan SQL Schema
1. Buka Supabase Dashboard > SQL Editor
2. Copy isi file `database/schema.sql`
3. Jalankan SQL (tanpa bagian demo data dulu)

#### C. Buat User Demo
1. Di Supabase Dashboard > Authentication > Users
2. Buat user baru:
   - Email: `demo@cfd.app`, Password: `demo12345`
   - Email: `member@cfd.app`, Password: `member12345`
   - Email: `admin@cfd.app`, Password: `admin12345`

#### D. Insert Profiles
1. Kembali ke SQL Editor
2. Insert profiles dengan UUID dari auth.users:

```sql
-- Ganti dengan UUID yang sebenarnya dari auth.users
INSERT INTO profiles (id, email, full_name, role) VALUES
    ('user-uuid-demo', 'demo@cfd.app', 'Demo User', 'demo_viewer'),
    ('user-uuid-member', 'member@cfd.app', 'Member User', 'member'),
    ('user-uuid-admin', 'admin@cfd.app', 'Admin User', 'admin');

-- Insert demo project (ganti owner_id dengan UUID demo user)
INSERT INTO projects (id, name, description, owner_id, is_demo) VALUES
    ('00000000-0000-0000-0000-000000000001', 'DEMO - CoffeeShop', 
     'Demo project showing customer feedback analysis for a coffee shop', 
     'user-uuid-demo', true);
```

### 4. Setup AI Services (Opsional)

#### A. HuggingFace
1. Daftar di [https://huggingface.co](https://huggingface.co)
2. Buat API token di Settings > Access Tokens
3. Tambahkan ke `.env` sebagai `HUGGINGFACE_API_TOKEN`

#### B. Replicate (untuk IBM Granite)
1. Daftar di [https://replicate.com](https://replicate.com)
2. Buat API token di Account > API tokens
3. Tambahkan ke `.env` sebagai `REPLICATE_API_TOKEN`

#### C. IBM Watson NLU (Opsional)
1. Daftar IBM Cloud di [https://cloud.ibm.com](https://cloud.ibm.com)
2. Buat instance Watson Natural Language Understanding
3. Copy API key dan URL ke `.env`

#### D. IBM Orchestrate (Opsional)
1. Akses IBM Orchestrate
2. Setup API credentials
3. Tambahkan ke `.env`

### 5. Jalankan Aplikasi

#### Menggunakan Script Setup (Direkomendasikan)
```bash
chmod +x setup.sh
./setup.sh
```

#### Manual dengan Docker Compose
```bash
# Build dan start services
docker-compose up -d

# Check logs jika ada masalah
docker-compose logs -f backend
docker-compose logs -f frontend
```

#### Manual tanpa Docker
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (terminal baru)
cd frontend
npm install
npm run dev
```

### 6. Test Setup

```bash
# Jalankan test script
chmod +x test-docker.sh
./test-docker.sh

# Manual test
curl http://localhost:8000/health
curl http://localhost:3000
```

### 7. Akses Aplikasi

- **Frontend**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

## 🔑 Login ke Aplikasi

Gunakan salah satu akun demo:

| Role | Email | Password | Fitur |
|------|-------|----------|-------|
| Demo | `demo@cfd.app` | `demo12345` | Read-only dashboard |
| Member | `member@cfd.app` | `member12345` | Full features |
| Admin | `admin@cfd.app` | `admin12345` | Admin access |

## 🔧 Troubleshooting

### Backend tidak bisa start
```bash
# Check logs
docker-compose logs backend

# Rebuild container
docker-compose build --no-cache backend
```

### Frontend tidak bisa diakses
```bash
# Check logs
docker-compose logs frontend

# Rebuild container
docker-compose build --no-cache frontend
```

### Database connection error
1. Pastikan SUPABASE_URL dan keys benar di `.env`
2. Pastikan schema sudah dijalankan
3. Check RLS policies di Supabase Dashboard

### AI Services tidak bekerja
1. Pastikan API tokens valid di `.env`
2. Check quota dan limits di provider
3. Lihat logs untuk error details

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Logs
```bash
# Semua services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f redis
```

### Performance
```bash
# Container stats
docker stats

# Disk usage
docker system df
```

## 🔄 Development Workflow

### Code Changes
1. Edit kode di editor favorit
2. Perubahan akan ter-reload otomatis (hot reload)
3. Test perubahan di browser

### Database Changes
1. Edit `database/schema.sql`
2. Jalankan migration di Supabase SQL Editor
3. Update models jika perlu

### Deployment
1. Commit changes ke git
2. Push ke GitHub
3. Deploy ke platform pilihan (Railway, Fly.io, dll)

## 🆘 Mendapatkan Bantuan

Jika mengalami masalah:

1. **Check Issues**: [GitHub Issues](https://github.com/mrhdayat/ai-customer-feedback/issues)
2. **Buat Issue Baru**: Sertakan logs dan error details
3. **Discord/Discussions**: [GitHub Discussions](https://github.com/mrhdayat/ai-customer-feedback/discussions)

## 🎯 Next Steps

Setelah setup berhasil:

1. **Explore Demo**: Login dengan akun demo dan jelajahi fitur
2. **Add Real Data**: Import feedback dari sumber nyata
3. **Configure AI**: Setup semua AI services untuk fitur lengkap
4. **Customize**: Sesuaikan dengan kebutuhan bisnis Anda
5. **Deploy**: Deploy ke production dengan panduan di `DEPLOYMENT.md`

## 🔐 Security Notes

- **Jangan commit `.env`** ke git (sudah ada di .gitignore)
- **Gunakan environment variables** untuk production
- **Rotate API keys** secara berkala
- **Enable RLS** di Supabase untuk security
- **Use HTTPS** di production

---

Selamat menggunakan Customer Feedback Dashboard! 🎉
