from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    DEMO_VIEWER = "demo_viewer"
    MEMBER = "member"
    ADMIN = "admin"


class FeedbackSource(str, Enum):
    MANUAL = "manual"
    TWITTER = "twitter"
    GOOGLE_MAPS = "google_maps"
    CSV_IMPORT = "csv_import"
    API = "api"


class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class UrgencyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Request Models
class FeedbackCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    source: FeedbackSource = FeedbackSource.MANUAL
    source_url: Optional[str] = None
    source_metadata: Optional[Dict[str, Any]] = {}
    author_name: Optional[str] = None
    author_handle: Optional[str] = None
    posted_at: Optional[datetime] = None
    language: str = "auto"


class FeedbackBatch(BaseModel):
    project_id: str
    feedbacks: List[FeedbackCreate]


class AnalysisRequest(BaseModel):
    feedback_id: str
    force_reanalysis: bool = False


class AnalysisBatchRequest(BaseModel):
    feedback_ids: List[str]
    force_reanalysis: bool = False


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    settings: Optional[Dict[str, Any]] = {}


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    settings: Optional[Dict[str, Any]] = None


# Response Models
class UserProfile(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    role: UserRole
    created_at: datetime
    updated_at: datetime


class Project(BaseModel):
    id: str
    name: str
    description: Optional[str]
    owner_id: str
    is_demo: bool
    settings: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class TopicScore(BaseModel):
    label: str
    score: float
    confidence: Optional[float] = None


class Entity(BaseModel):
    text: str
    type: str
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = {}


class GraniteInsights(BaseModel):
    urgency: UrgencyLevel
    action_recommendation: str
    confidence: Optional[float] = None
    reasoning: Optional[str] = None


class Analysis(BaseModel):
    id: str
    feedback_id: str
    detected_language: Optional[str]
    sentiment_label: Optional[SentimentLabel]
    sentiment_score: Optional[float]
    sentiment_confidence: Optional[float]
    sentiment_model: Optional[str]
    topics: List[TopicScore]
    topics_fixed: List[TopicScore]
    entities: List[Entity]
    keywords: List[Dict[str, Any]]
    categories: List[Dict[str, Any]]
    granite_summary: Optional[str]
    granite_insights: Optional[GraniteInsights]
    granite_tie_break: Optional[Dict[str, Any]]
    processing_time_ms: Optional[int]
    errors: List[str]
    created_at: datetime
    updated_at: datetime


class Feedback(BaseModel):
    id: str
    project_id: str
    content: str
    source: FeedbackSource
    source_url: Optional[str]
    source_metadata: Dict[str, Any]
    author_name: Optional[str]
    author_handle: Optional[str]
    posted_at: Optional[datetime]
    language: str
    created_at: datetime
    updated_at: datetime
    analysis: Optional[Analysis] = None


class OrchestrateJob(BaseModel):
    id: str
    feedback_id: str
    analysis_id: str
    kind: str
    status: JobStatus
    payload: Dict[str, Any]
    response: Dict[str, Any]
    external_ref: Optional[str]
    error_message: Optional[str]
    retry_count: int
    max_retries: int
    scheduled_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class ProjectSummary(BaseModel):
    total_feedbacks: int
    sentiment_distribution: Dict[str, int]
    top_topics: List[Dict[str, Any]]
    recent_trends: List[Dict[str, Any]]
    top_entities: List[Dict[str, Any]]
    urgency_distribution: Dict[str, int]
    automation_stats: Dict[str, int]


class PaginatedResponse(BaseModel):
    data: List[Any]
    total: int
    page: int
    per_page: int
    total_pages: int


# API Response Models
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[List[str]] = None


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    services: Dict[str, str]


# Language Detection
class LanguageDetection(BaseModel):
    language: str
    confidence: float


# AI Service Models
class SentimentResult(BaseModel):
    label: SentimentLabel
    score: float
    confidence: float
    model: str


class TopicResult(BaseModel):
    topics: List[TopicScore]
    model: str
    threshold: float


class EntityResult(BaseModel):
    entities: List[Entity]
    keywords: List[Dict[str, Any]]
    categories: List[Dict[str, Any]]
    service: str


class GraniteResult(BaseModel):
    summary: str
    topics_fixed: List[TopicScore]
    tie_break: Optional[Dict[str, Any]]
    insights: GraniteInsights
    raw_response: str
