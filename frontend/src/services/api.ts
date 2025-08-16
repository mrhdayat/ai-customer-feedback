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
    return this.request<ProjectSummary>(`/api/projects/${id}/summary`)
  }

  async getProjectFeedbacks(
    id: string, 
    page = 1, 
    perPage = 20,
    filters: { source?: string; sentiment?: string; topic?: string } = {}
  ) {
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
