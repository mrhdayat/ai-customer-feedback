export interface User {
  id: string
  email: string
  full_name?: string
  avatar_url?: string
  role: 'demo_viewer' | 'member' | 'admin'
  created_at: string
  updated_at: string
}

export interface Project {
  id: string
  name: string
  description?: string
  owner_id: string
  is_demo: boolean
  settings: Record<string, any>
  created_at: string
  updated_at: string
}

export interface Feedback {
  id: string
  project_id: string
  content: string
  source: 'manual' | 'twitter' | 'google_maps' | 'csv_import' | 'api'
  source_url?: string
  source_metadata: Record<string, any>
  author_name?: string
  author_handle?: string
  posted_at?: string
  language: string
  created_at: string
  updated_at: string
  analysis?: Analysis
}

export interface Analysis {
  id: string
  feedback_id: string
  detected_language?: string
  sentiment_label?: 'positive' | 'negative' | 'neutral'
  sentiment_score?: number
  sentiment_confidence?: number
  sentiment_model?: string
  topics: TopicScore[]
  topics_fixed: TopicScore[]
  entities: Entity[]
  keywords: any[]
  categories: any[]
  granite_summary?: string
  granite_insights?: GraniteInsights
  granite_tie_break?: any
  processing_time_ms?: number
  errors: string[]
  created_at: string
  updated_at: string
}

export interface TopicScore {
  label: string
  score: number
  confidence?: number
}

export interface Entity {
  text: string
  type: string
  confidence?: number
  metadata?: Record<string, any>
}

export interface GraniteInsights {
  urgency: 'low' | 'medium' | 'high'
  action_recommendation: string
  confidence?: number
  reasoning?: string
}

export interface OrchestrateJob {
  id: string
  feedback_id: string
  analysis_id: string
  kind: string
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'cancelled'
  payload: Record<string, any>
  response: Record<string, any>
  external_ref?: string
  error_message?: string
  retry_count: number
  max_retries: number
  scheduled_at: string
  started_at?: string
  completed_at?: string
  created_at: string
  updated_at: string
}

export interface ProjectSummary {
  total_feedbacks: number
  sentiment_distribution: Record<string, number>
  top_topics: Array<{ label: string; count: number }>
  recent_trends: Array<any>
  top_entities: Array<any>
  urgency_distribution: Record<string, number>
  automation_stats: Record<string, number>
}

export interface APIResponse<T = any> {
  success: boolean
  message: string
  data?: T
  errors?: string[]
}

export interface PaginationInfo {
  total: number
  page: number
  per_page: number
  total_pages: number
}

export interface PaginatedResponse<T> {
  data: T[]
  pagination: PaginationInfo
}
