import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { 
  ArrowRight, 
  BarChart3, 
  Brain, 
  Globe, 
  Zap, 
  Shield, 
  CheckCircle,
  Play,
  Star
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export function LandingPage() {
  const features = [
    {
      icon: Brain,
      title: 'AI Multi-Bahasa',
      description: 'Analisis sentimen untuk Bahasa Indonesia dan internasional dengan akurasi tinggi'
    },
    {
      icon: BarChart3,
      title: 'Zero-Shot Topics',
      description: 'Klasifikasi topik otomatis tanpa perlu training data khusus'
    },
    {
      icon: Globe,
      title: 'IBM Watson NLU',
      description: 'Ekstraksi entitas dan konsep menggunakan teknologi AI terdepan'
    },
    {
      icon: Zap,
      title: 'Automasi Tindakan',
      description: 'Workflow otomatis via IBM Orchestrate untuk respon cepat'
    },
    {
      icon: Shield,
      title: 'Keamanan Tinggi',
      description: 'RLS Policies, HTTPS, CSP ketat, dan audit log lengkap'
    },
    {
      icon: CheckCircle,
      title: 'Real-time Dashboard',
      description: 'Visualisasi data dan insights yang dapat diakses secara real-time'
    }
  ]

  const howItWorks = [
    {
      step: '01',
      title: 'Tempel Ulasan',
      description: 'Upload ulasan dari Twitter/X, Google Maps, atau input manual',
      color: 'bg-blue-500'
    },
    {
      step: '02',
      title: 'Analisis AI',
      description: 'Sistem AI menganalisis sentimen, topik, dan entitas secara otomatis',
      color: 'bg-green-500'
    },
    {
      step: '03',
      title: 'Dapatkan Insight',
      description: 'Terima ringkasan, rekomendasi tindakan, dan prioritas urgency',
      color: 'bg-purple-500'
    },
    {
      step: '04',
      title: 'Otomasi Tindak Lanjut',
      description: 'Sistem otomatis membuat tiket, alert, atau assign ke tim yang tepat',
      color: 'bg-orange-500'
    }
  ]

  const comparison = [
    { feature: 'Lihat dashboard contoh', demo: true, member: true },
    { feature: 'Filter & sort data', demo: true, member: true },
    { feature: 'Lihat summary & insights', demo: true, member: true },
    { feature: 'Import data sendiri', demo: false, member: true },
    { feature: 'Jalankan analisis AI', demo: false, member: true },
    { feature: 'Export data CSV', demo: false, member: true },
    { feature: 'Trigger automasi', demo: false, member: true },
    { feature: 'Kelola multiple proyek', demo: false, member: true },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      {/* Header */}
      <header className="border-b border-blue-100 bg-white/80 backdrop-blur-sm sticky top-0 z-40">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <BarChart3 className="h-8 w-8 text-blue-600" />
              <span className="text-xl font-bold text-gray-900">Customer Feedback Dashboard</span>
            </div>
            
            <div className="flex items-center space-x-4">
              <Link to="/demo">
                <Button variant="ghost" className="flex items-center space-x-2">
                  <Play className="h-4 w-4" />
                  <span>Coba Demo</span>
                </Button>
              </Link>
              <Link to="/login">
                <Button className="flex items-center space-x-2">
                  <span>Masuk</span>
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center max-w-4xl mx-auto"
        >
          <h1 className="text-5xl font-bold text-gray-900 mb-6 leading-tight">
            Customer Feedback Dashboard
            <span className="block text-blue-600 mt-2">AI siap aksi untuk ulasan Indonesia & global</span>
          </h1>
          
          <p className="text-xl text-gray-600 mb-10 leading-relaxed">
            Analisis sentimen multi-bahasa, klasifikasi topik otomatis, ekstraksi entitas dengan IBM Watson NLU, 
            dan automasi tindak lanjut via IBM Orchestrate. Semua dalam satu dashboard yang mudah digunakan.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/demo">
              <Button size="lg" variant="outline" className="flex items-center space-x-2">
                <Play className="h-5 w-5" />
                <span>Coba Demo</span>
              </Button>
            </Link>
            <Link to="/login">
              <Button size="lg" className="flex items-center space-x-2">
                <span>Buat Akun Gratis</span>
                <ArrowRight className="h-5 w-5" />
              </Button>
            </Link>
          </div>
        </motion.div>
      </section>

      {/* How It Works */}
      <section className="bg-white py-20">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Cara Kerja Sistem</h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              4 langkah sederhana untuk mengubah ulasan pelanggan menjadi insight yang dapat ditindaklanjuti
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {howItWorks.map((step, index) => (
              <motion.div
                key={step.step}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="text-center"
              >
                <div className={`w-16 h-16 ${step.color} rounded-full flex items-center justify-center mx-auto mb-4`}>
                  <span className="text-2xl font-bold text-white">{step.step}</span>
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">{step.title}</h3>
                <p className="text-gray-600">{step.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Key Features */}
      <section className="py-20 bg-gray-50">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Fitur Unggulan</h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Teknologi AI terdepan untuk analisis feedback pelanggan yang komprehensif
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                viewport={{ once: true }}
              >
                <Card className="h-full hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <feature.icon className="h-12 w-12 text-blue-600 mb-4" />
                    <CardTitle className="text-xl">{feature.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <CardDescription className="text-base">
                      {feature.description}
                    </CardDescription>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Demo vs Member Comparison */}
      <section className="py-20 bg-white">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Demo vs Member</h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Bandingkan fitur yang tersedia untuk akun demo dan member
            </p>
          </motion.div>

          <div className="max-w-4xl mx-auto">
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              <div className="grid grid-cols-3 bg-gray-50 p-4 font-semibold text-gray-900">
                <div>Fitur</div>
                <div className="text-center">Demo</div>
                <div className="text-center">Member</div>
              </div>
              
              {comparison.map((item, index) => (
                <motion.div
                  key={item.feature}
                  initial={{ opacity: 0 }}
                  whileInView={{ opacity: 1 }}
                  transition={{ duration: 0.4, delay: index * 0.05 }}
                  viewport={{ once: true }}
                  className="grid grid-cols-3 p-4 border-t border-gray-100 hover:bg-gray-50"
                >
                  <div className="text-gray-900">{item.feature}</div>
                  <div className="text-center">
                    {item.demo ? (
                      <CheckCircle className="h-5 w-5 text-green-500 mx-auto" />
                    ) : (
                      <span className="text-gray-300">—</span>
                    )}
                  </div>
                  <div className="text-center">
                    {item.member ? (
                      <CheckCircle className="h-5 w-5 text-green-500 mx-auto" />
                    ) : (
                      <span className="text-gray-300">—</span>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>

            <div className="text-center mt-8">
              <Link to="/login">
                <Button size="lg" className="flex items-center space-x-2 mx-auto">
                  <span>Mulai dengan Akun Member</span>
                  <ArrowRight className="h-5 w-5" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Security & Privacy */}
      <section className="py-20 bg-blue-50">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center"
          >
            <Shield className="h-16 w-16 text-blue-600 mx-auto mb-6" />
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Keamanan & Privasi</h2>
            <p className="text-lg text-gray-600 max-w-3xl mx-auto">
              Data Anda aman dengan enkripsi HTTPS, Content Security Policy yang ketat, 
              Row Level Security (RLS) di database, rate limiting, dan audit log lengkap. 
              Token AI tidak pernah diekspos ke frontend.
            </p>
          </motion.div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
        <div className="container mx-auto px-4 text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl font-bold mb-4">Siap Menganalisis Feedback Pelanggan?</h2>
            <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
              Mulai sekarang dengan akun gratis dan rasakan kekuatan AI untuk memahami pelanggan Anda
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/demo">
                <Button size="lg" variant="outline" className="bg-white text-blue-600 hover:bg-gray-100 flex items-center space-x-2">
                  <Play className="h-5 w-5" />
                  <span>Coba Demo Dulu</span>
                </Button>
              </Link>
              <Link to="/login">
                <Button size="lg" className="bg-white text-blue-600 hover:bg-gray-100 flex items-center space-x-2">
                  <span>Buat Akun Gratis</span>
                  <ArrowRight className="h-5 w-5" />
                </Button>
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <BarChart3 className="h-8 w-8 text-blue-400" />
                <span className="text-xl font-bold">CFD</span>
              </div>
              <p className="text-gray-400">
                Customer Feedback Dashboard dengan teknologi AI terdepan untuk analisis feedback multi-bahasa.
              </p>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold mb-4">Fitur</h3>
              <ul className="space-y-2 text-gray-400">
                <li>Analisis Sentimen AI</li>
                <li>Klasifikasi Topik</li>
                <li>Ekstraksi Entitas</li>
                <li>Automasi Workflow</li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold mb-4">Dukungan</h3>
              <ul className="space-y-2 text-gray-400">
                <li>
                  <Link to="/docs" className="hover:text-white transition-colors">
                    Dokumentasi API
                  </Link>
                </li>
                <li>
                  <a href="mailto:support@cfd.app" className="hover:text-white transition-colors">
                    Kontak Support
                  </a>
                </li>
                <li>
                  <Link to="/privacy" className="hover:text-white transition-colors">
                    Kebijakan Privasi
                  </Link>
                </li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2024 Customer Feedback Dashboard. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
