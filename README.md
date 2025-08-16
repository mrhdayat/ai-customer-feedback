# Customer Feedback Dashboard (CFD)

Sistem analisis feedback pelanggan berbasis AI yang mendukung Bahasa Indonesia dan bahasa internasional.

## 🎯 Fitur Utama

- **📊 Analisis Sentimen Multi-Bahasa** (Indonesia & English)
- **🎯 Klasifikasi Topik Zero-Shot** otomatis
- **🔍 Ekstraksi Entitas** via IBM Watson NLU
- **🤖 Ringkasan & Rekomendasi AI** via IBM Granite 3.3-8B
- **⚡ Otomasi Tindak Lanjut** via IBM Orchestrate
- **👥 Kontrol Akses Berbasis Role** (Demo, Member, Admin)

## 🛠️ Teknologi

### Frontend

- React + Vite (TypeScript)
- TailwindCSS + ShadCN UI
- React Query, Zustand, Framer Motion
- TanStack Table, Recharts

### Backend

- FastAPI (Python)
- Supabase (PostgreSQL + Auth)
- AI Services: HuggingFace, IBM Watson NLU, Replicate, IBM Orchestrate

## 🚀 Quick Start

### Menggunakan Docker (Direkomendasikan)

```bash
# Clone repository
git clone https://github.com/mrhdayat/ai-customer-feedback.git
cd ai-customer-feedback

# Copy file environment
cp env.example .env
# Edit .env dengan API keys Anda

# Jalankan setup otomatis
chmod +x setup.sh
./setup.sh

# Atau mulai manual
docker-compose up -d

# Test setup
chmod +x test-docker.sh
./test-docker.sh

# Akses aplikasi
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# Dokumentasi API: http://localhost:8000/docs
```

### Setup Manual

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

### Deploy Production

```bash
# Build dan jalankan production
docker-compose -f docker-compose.prod.yml up -d

# Lihat DEPLOYMENT.md untuk panduan platform-specific:
# - Railway
# - Fly.io
# - DigitalOcean
# - VPS deployment
```

## 🔑 Akun Demo

| Role   | Email            | Password      | Level Akses   |
| ------ | ---------------- | ------------- | ------------- |
| Demo   | `demo@cfd.app`   | `demo12345`   | Read-only     |
| Member | `member@cfd.app` | `member12345` | Fitur lengkap |
| Admin  | `admin@cfd.app`  | `admin12345`  | Akses admin   |

## ⚙️ Konfigurasi Environment

Lihat `env.example` untuk konfigurasi yang diperlukan. Variabel utama:

```bash
# Wajib
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Opsional tapi direkomendasikan untuk fitur AI lengkap
HUGGINGFACE_API_TOKEN=your-hf-token
IBM_WATSON_NLU_API_KEY=your-watson-api-key
REPLICATE_API_TOKEN=your-replicate-token
IBM_ORCHESTRATE_API_KEY=your-orchestrate-api-key
```

## 🗄️ Setup Database

1. Buat project Supabase baru
2. Jalankan SQL schema dari `database/schema.sql`
3. Buat user demo melalui Supabase Auth Dashboard:
   - `demo@cfd.app` dengan password `demo12345`
   - `member@cfd.app` dengan password `member12345`
   - `admin@cfd.app` dengan password `admin12345`
4. Insert profiles dan data demo sesuai instruksi di schema
5. Konfigurasi environment variables
6. Mulai aplikasi

## 📖 Dokumentasi

- **Dokumentasi API Interaktif**: `http://localhost:8000/docs`
- **Panduan API Lengkap**: Lihat `API.md`
- **Panduan Deployment**: Lihat `DEPLOYMENT.md`

## 📁 Struktur Project

```
ai-customer-feedback/
├── backend/              # FastAPI backend
│   ├── main.py          # Aplikasi utama
│   ├── models.py        # Model Pydantic
│   ├── database.py      # Operasi database
│   ├── services/        # Integrasi AI services
│   └── routers/         # Handler API routes
├── frontend/            # React + Vite frontend
│   ├── src/
│   │   ├── components/  # Komponen reusable
│   │   ├── pages/       # Komponen halaman
│   │   ├── services/    # API client
│   │   └── store/       # State management
├── database/            # Schema database
├── docker-compose.yml   # Setup development
├── docker-compose.prod.yml # Setup production
└── setup.sh            # Script setup otomatis
```

## 🤖 Pipeline AI

### 1. Deteksi Bahasa

- **Library**: `langdetect` + `langid`
- **Output**: Kode bahasa (id/en/dll) dengan confidence score

### 2. Analisis Sentimen

- **Indonesia**: `cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual`
- **English**: `distilbert-base-uncased-finetuned-sst-2-english`
- **Threshold confidence**: 0.6

### 3. Klasifikasi Topik

- **Model**: `facebook/bart-large-mnli`
- **Method**: Zero-shot multi-label classification
- **Threshold**: 0.35
- **Kategori**: harga, layanan, produk, pengiriman, lokasi, kualitas, after-sales

### 4. Ekstraksi Entitas

- **Service**: IBM Watson NLU
- **Fitur**: entities, keywords, categories
- **Dukungan bahasa**: 12+ bahasa

### 5. Insights & Rekomendasi

- **Model**: IBM Granite 3.3-8B Instruct (via Replicate)
- **Output**: Summary, topik refined, urgency level, rekomendasi tindakan

### 6. Otomasi Workflow

- **Service**: IBM Orchestrate
- **Trigger**: Berdasarkan urgency dan topik
- **Actions**: Pembuatan tiket, alert, assignment

## 🔄 Development

```bash
# Mulai development servers
docker-compose up -d

# Lihat logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Jalankan tests
./test-docker.sh

# Stop services
docker-compose down
```

## 🔒 Keamanan

- ✅ HTTPS enforcement
- ✅ Content Security Policy (CSP) headers
- ✅ Rate limiting per IP/User (60 req/menit)
- ✅ Input sanitization (Zod + Pydantic)
- ✅ JWT authentication
- ✅ Row Level Security (RLS) di database
- ✅ Audit logging

## 🎨 UI/UX Features

- 🌟 Landing page dengan animasi (Framer Motion)
- 📊 Dashboard dengan visualisasi data real-time
- 🌙 Dark mode support
- 📱 Responsive design
- 🎯 Mode demo dengan read-only access
- ⚡ Loading states dan error handling
- 🔔 Toast notifications

## 📊 Analytics & Monitoring

- **Health Check**: `/health` endpoint
- **Metrics**: Prometheus metrics di `/metrics`
- **Logging**: Structured logging via Docker
- **Performance**: Request timing dan rate limiting stats

## 🌐 API Endpoints

### Authentication

- `POST /api/auth/login` - Login dengan email/password
- `GET /api/auth/demo-tokens` - Generate demo tokens (dev only)

### Projects

- `GET /api/projects` - List projects dengan pagination
- `POST /api/projects` - Buat project baru (Member/Admin)
- `GET /api/projects/:id/summary` - Analytics summary

### Feedbacks

- `POST /api/feedbacks` - Tambah feedback
- `POST /api/feedbacks/:id/analyze` - Analisis AI
- `POST /api/feedbacks/analyze/batch` - Analisis batch

### Orchestrate

- `GET /api/orchestrate/jobs` - List automation jobs
- `POST /api/orchestrate/trigger/:feedback_id` - Trigger manual automation

## 🚀 Deployment Options

### 1. Railway (Direkomendasikan)

```bash
# Deploy otomatis via GitHub integration
# Lihat DEPLOYMENT.md untuk detail lengkap
```

### 2. Docker Compose Production

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 3. Platform Cloud Lainnya

- **Fly.io**: Panduan lengkap di DEPLOYMENT.md
- **DigitalOcean**: App Platform integration
- **VPS Manual**: Setup dengan Nginx reverse proxy

## 🧪 Testing

```bash
# Test setup Docker
./test-docker.sh

# Test API endpoints
curl http://localhost:8000/health

# Test frontend
curl http://localhost:3000
```

## 🤝 Contributing

1. Fork repository ini
2. Buat feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push ke branch (`git push origin feature/AmazingFeature`)
5. Buat Pull Request

## 👨‍💻 Author

**mrhdayat**

- GitHub: [@mrhdayat](https://github.com/mrhdayat)
- Repository: [ai-customer-feedback](https://github.com/mrhdayat/ai-customer-feedback)

## 🙏 Acknowledgments

- [Supabase](https://supabase.io/) untuk database dan auth
- [HuggingFace](https://huggingface.co/) untuk AI models
- [IBM Watson NLU](https://www.ibm.com/watson/natural-language-understanding) untuk entity extraction
- [Replicate](https://replicate.com/) untuk IBM Granite model hosting
- [IBM Orchestrate](https://www.ibm.com/watson-orchestrate) untuk workflow automation
- [ShadCN UI](https://ui.shadcn.com/) untuk komponen UI yang cantik

## 🔧 Troubleshooting

### Error Database Connection

```bash
# Check Supabase connection
docker-compose logs backend | grep -i database
```

### Error AI Services

```bash
# Check API keys dalam .env
cat .env | grep API
```

### Error Frontend Build

```bash
# Clear cache dan rebuild
docker-compose build --no-cache frontend
```

### Rate Limiting Issues

```bash
# Check Redis
docker-compose exec redis redis-cli monitor
```

## 📞 Support

Jika Anda mengalami masalah atau memiliki pertanyaan:

1. Cek [Issues](https://github.com/mrhdayat/ai-customer-feedback/issues) yang sudah ada
2. Buat issue baru dengan template yang sesuai
3. Untuk pertanyaan umum, gunakan [Discussions](https://github.com/mrhdayat/ai-customer-feedback/discussions)

---

⭐ **Jika project ini membantu Anda, jangan lupa beri star!** ⭐
