import { useAuthStore, getAuthHeader } from '@/store/auth'
import { 
  APIResponse, 
  User, 
  Project, 
  Feedback, 
  Analysis, 
  ProjectSummary,
  OrchestrateJob,
} from '@/types'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'
const IS_DEMO_MODE = !import.meta.env.VITE_BACKEND_URL || import.meta.env.VITE_DEMO_MODE === 'true'

// Mock data untuk demo mode
const MOCK_DATA = {
  user: {
    id: 'demo-user-id',
    email: 'demo@cfd.app',
    full_name: 'Demo User',
    role: 'demo_viewer' as const,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  projects: [
    {
      id: 'demo-project-1',
      name: 'DEMO - CoffeeShop',
      description: 'Demo project showing customer feedback analysis for a coffee shop',
      owner_id: 'demo-user-id',
      is_demo: true,
      settings: { theme: 'default' },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
  ],
  feedbacks: [
    {
      id: 'feedback-1',
      project_id: 'demo-project-1',
      content: 'Kopi di sini enak banget! Pelayanannya juga cepat. Recommended!',
      source: 'google_maps' as const,
      source_metadata: { rating: 5 },
      author_name: 'Sarah M.',
      posted_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      language: 'id',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      analysis: {
        id: 'analysis-1',
        feedback_id: 'feedback-1',
        detected_language: 'id',
        sentiment_label: 'positive' as const,
        sentiment_score: 0.89,
        sentiment_confidence: 0.94,
        sentiment_model: 'cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual',
        topics: [
          { label: 'service', score: 0.92 },
          { label: 'product', score: 0.85 }
        ],
        topics_fixed: [
          { label: 'layanan', score: 0.92 },
          { label: 'produk', score: 0.85 }
        ],
        entities: [
          { text: 'kopi', type: 'product', confidence: 0.9 }
        ],
        keywords: ['kopi', 'pelayanan'],
        categories: ['food_beverage'],
        granite_summary: 'Feedback positif tentang kualitas kopi dan pelayanan yang cepat.',
        granite_insights: {
          urgency: 'low' as const,
          action_recommendation: 'Gunakan sebagai testimonial positif untuk marketing.',
          confidence: 0.88
        },
        processing_time_ms: 1250,
        errors: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
    },
    {
      id: 'feedback-2', 
      project_id: 'demo-project-1',
      content: 'Disappointing experience. Coffee was cold and service was slow. Will not return.',
      source: 'twitter' as const,
      source_metadata: { followers: 1200 },
      author_name: 'John D.',
      author_handle: '@johnd',
      posted_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      language: 'en',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      analysis: {
        id: 'analysis-2',
        feedback_id: 'feedback-2',
        detected_language: 'en',
        sentiment_label: 'negative' as const,
        sentiment_score: 0.82,
        sentiment_confidence: 0.91,
        sentiment_model: 'distilbert-base-uncased-finetuned-sst-2-english',
        topics: [
          { label: 'service', score: 0.88 },
          { label: 'product', score: 0.76 }
        ],
        topics_fixed: [
          { label: 'service', score: 0.88 },
          { label: 'product', score: 0.76 }
        ],
        entities: [
          { text: 'coffee', type: 'product', confidence: 0.95 }
        ],
        keywords: ['coffee', 'service', 'slow'],
        categories: ['food_beverage'],
        granite_summary: 'Keluhan tentang kopi dingin dan pelayanan lambat. Customer menyatakan tidak akan kembali.',
        granite_insights: {
          urgency: 'high' as const,
          action_recommendation: 'Segera follow up customer dan perbaiki proses pelayanan.',
          confidence: 0.92
        },
        processing_time_ms: 1150,
        errors: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
    },
    {
      id: 'feedback-3',
      project_id: 'demo-project-1', 
      content: 'Tempatnya cozy, tapi harganya agak mahal untuk ukuran porsi segitu. Wifi juga lambat.',
      source: 'manual' as const,
      source_metadata: { channel: 'walk_in' },
      author_name: 'Rina S.',
      posted_at: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
      language: 'id',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      analysis: {
        id: 'analysis-3',
        feedback_id: 'feedback-3',
        detected_language: 'id',
        sentiment_label: 'neutral' as const,
        sentiment_score: 0.65,
        sentiment_confidence: 0.78,
        sentiment_model: 'cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual',
        topics: [
          { label: 'price', score: 0.91 },
          { label: 'location', score: 0.73 }
        ],
        topics_fixed: [
          { label: 'harga', score: 0.91 },
          { label: 'lokasi', score: 0.73 }
        ],
        entities: [
          { text: 'wifi', type: 'service', confidence: 0.87 }
        ],
        keywords: ['harga', 'porsi', 'wifi'],
        categories: ['food_beverage'],
        granite_summary: 'Feedback mixed tentang ambience positif tapi concerns tentang harga dan wifi.',
        granite_insights: {
          urgency: 'medium' as const,
          action_recommendation: 'Review pricing strategy dan upgrade infrastruktur wifi.',
          confidence: 0.81
        },
        processing_time_ms: 1340,
        errors: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
    }
  ],
  summary: {
    total_feedbacks: 3,
    sentiment_distribution: {
      positive: 1,
      negative: 1,
      neutral: 1
    },
    top_topics: [
      { label: 'service', count: 2 },
      { label: 'product', count: 2 },
      { label: 'price', count: 1 },
      { label: 'location', count: 1 }
    ],
    urgency_distribution: {
      high: 1,
      medium: 1,
      low: 1
    },
    automation_stats: {
      completed: 2,
      pending: 1,
      failed: 0
    }
  }
}

class APIClient {
  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<APIResponse<T>> {
    const url = `${API_BASE_URL}${endpoint}`
    
    const authHeader = getAuthHeader()
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    }
    
    // Add auth header if it exists
    if (authHeader && authHeader.Authorization) {
      headers.Authorization = authHeader.Authorization
    }
    
    const config: RequestInit = {
      headers,
      ...options,
    }

    try {
      const response = await fetch(url, config)
      const data = await response.json()

      if (!response.ok) {
        // Handle specific error cases
        if (response.status === 401) {
          // Token expired or invalid
          useAuthStore.getState().logout()
          throw new Error('Authentication required')
        }
        
        throw new Error(data.message || `HTTP ${response.status}`)
      }

      return data
    } catch (error) {
      console.error('API request failed:', error)
      throw error
    }
  }

  // Auth endpoints
  async login(email: string, password: string) {
    // Demo mode - bypass backend call
    if (IS_DEMO_MODE) {
      await new Promise(resolve => setTimeout(resolve, 1000)) // Simulate loading
      
      if (email === 'demo@cfd.app' && password === 'demo12345') {
        return {
          data: {
            access_token: 'demo-token-' + Date.now(),
            user: MOCK_DATA.user
          },
          success: true,
          message: 'Login successful (Demo Mode)'
        }
      } else {
        throw new Error('Invalid demo credentials. Use demo@cfd.app / demo12345')
      }
    }
    
    return this.request<{ access_token: string; user: User }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
  }

  async logout() {
    return this.request('/api/auth/logout', { method: 'POST' })
  }

  async getDemoTokens() {
    return this.request<Record<string, string>>('/api/auth/demo-tokens')
  }

  // Projects endpoints
  async getProjects(page = 1, perPage = 10) {
    if (IS_DEMO_MODE) {
      await new Promise(resolve => setTimeout(resolve, 500))
      return {
        data: {
          projects: MOCK_DATA.projects,
          pagination: { total: 1, page: 1, per_page: 10, pages: 1 }
        },
        success: true,
        message: 'Projects retrieved (Demo Mode)'
      }
    }
    
    return this.request<{
      projects: Project[]
      pagination: any
    }>(`/api/projects?page=${page}&per_page=${perPage}`)
  }

  async getProject(id: string) {
    return this.request<Project>(`/api/projects/${id}`)
  }

  async createProject(data: { name: string; description?: string }) {
    return this.request<Project>('/api/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateProject(id: string, data: Partial<Project>) {
    return this.request<Project>(`/api/projects/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteProject(id: string) {
    return this.request(`/api/projects/${id}`, { method: 'DELETE' })
  }

  async getProjectSummary(id: string) {
    if (IS_DEMO_MODE) {
      await new Promise(resolve => setTimeout(resolve, 800))
      return {
        data: MOCK_DATA.summary,
        success: true,
        message: 'Project summary retrieved (Demo Mode)'
      }
    }
    
    return this.request<ProjectSummary>(`/api/projects/${id}/summary`)
  }

  async getProjectFeedbacks(
    id: string, 
    page = 1, 
    perPage = 20,
    filters: { source?: string; sentiment?: string; topic?: string } = {}
  ) {
    if (IS_DEMO_MODE) {
      await new Promise(resolve => setTimeout(resolve, 600))
      return {
        data: {
          feedbacks: MOCK_DATA.feedbacks,
          pagination: { total: 3, page: 1, per_page: 20, pages: 1 },
          filters: {}
        },
        success: true,
        message: 'Feedbacks retrieved (Demo Mode)'
      }
    }
    
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
      ...Object.fromEntries(Object.entries(filters).filter(([_, v]) => v))
    })
    
    return this.request<{
      feedbacks: Feedback[]
      pagination: any
      filters: any
    }>(`/api/projects/${id}/feedbacks?${params}`)
  }

  // Feedbacks endpoints
  async createFeedback(projectId: string, data: {
    content: string
    source?: string
    source_url?: string
    author_name?: string
    author_handle?: string
    language?: string
  }) {
    return this.request<Feedback>(`/api/feedbacks?project_id=${projectId}`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async createFeedbackBatch(projectId: string, feedbacks: any[]) {
    return this.request(`/api/feedbacks/batch?project_id=${projectId}`, {
      method: 'POST',
      body: JSON.stringify(feedbacks),
    })
  }

  async getFeedback(id: string) {
    return this.request<Feedback>(`/api/feedbacks/${id}`)
  }

  async analyzeFeedback(id: string, forceReanalysis = false) {
    return this.request<Analysis>(`/api/feedbacks/${id}/analyze`, {
      method: 'POST',
      body: JSON.stringify({ feedback_id: id, force_reanalysis: forceReanalysis }),
    })
  }

  async analyzeFeedbackBatch(feedbackIds: string[], forceReanalysis = false) {
    return this.request('/api/feedbacks/analyze/batch', {
      method: 'POST',
      body: JSON.stringify({ feedback_ids: feedbackIds, force_reanalysis: forceReanalysis }),
    })
  }

  async deleteFeedback(id: string) {
    return this.request(`/api/feedbacks/${id}`, { method: 'DELETE' })
  }

  // Orchestrate endpoints
  async getOrchestrateJobs(
    projectId?: string,
    status?: string,
    page = 1,
    perPage = 20
  ) {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
    })
    
    if (projectId) params.append('project_id', projectId)
    if (status) params.append('status_filter', status)
    
    return this.request<{
      jobs: OrchestrateJob[]
      pagination: any
    }>(`/api/orchestrate/jobs?${params}`)
  }

  async retryOrchestrateJob(id: string) {
    return this.request(`/api/orchestrate/jobs/${id}/retry`, { method: 'POST' })
  }

  async cancelOrchestrateJob(id: string) {
    return this.request(`/api/orchestrate/jobs/${id}/cancel`, { method: 'POST' })
  }

  async triggerManualOrchestrate(feedbackId: string, jobKind: string) {
    return this.request(`/api/orchestrate/trigger/${feedbackId}?job_kind=${jobKind}`, {
      method: 'POST',
    })
  }

  async getAvailableSkills() {
    return this.request('/api/orchestrate/skills')
  }

  // Health check
  async healthCheck() {
    return this.request('/health')
  }
}

export const apiClient = new APIClient()

// Export commonly used API calls as hooks-ready functions
export const api = {
  // Auth
  login: apiClient.login.bind(apiClient),
  logout: apiClient.logout.bind(apiClient),
  getDemoTokens: apiClient.getDemoTokens.bind(apiClient),

  // Projects
  getProjects: apiClient.getProjects.bind(apiClient),
  getProject: apiClient.getProject.bind(apiClient),
  createProject: apiClient.createProject.bind(apiClient),
  updateProject: apiClient.updateProject.bind(apiClient),
  deleteProject: apiClient.deleteProject.bind(apiClient),
  getProjectSummary: apiClient.getProjectSummary.bind(apiClient),
  getProjectFeedbacks: apiClient.getProjectFeedbacks.bind(apiClient),

  // Feedbacks
  createFeedback: apiClient.createFeedback.bind(apiClient),
  createFeedbackBatch: apiClient.createFeedbackBatch.bind(apiClient),
  getFeedback: apiClient.getFeedback.bind(apiClient),
  analyzeFeedback: apiClient.analyzeFeedback.bind(apiClient),
  analyzeFeedbackBatch: apiClient.analyzeFeedbackBatch.bind(apiClient),
  deleteFeedback: apiClient.deleteFeedback.bind(apiClient),

  // Orchestrate
  getOrchestrateJobs: apiClient.getOrchestrateJobs.bind(apiClient),
  retryOrchestrateJob: apiClient.retryOrchestrateJob.bind(apiClient),
  cancelOrchestrateJob: apiClient.cancelOrchestrateJob.bind(apiClient),
  triggerManualOrchestrate: apiClient.triggerManualOrchestrate.bind(apiClient),
  getAvailableSkills: apiClient.getAvailableSkills.bind(apiClient),

  // Health
  healthCheck: apiClient.healthCheck.bind(apiClient),
}
