from supabase import create_client, Client
from config import settings
import logging

logger = logging.getLogger(__name__)

# Supabase client instances
supabase: Client = create_client(settings.supabase_url, settings.supabase_anon_key)
supabase_admin: Client = create_client(settings.supabase_url, settings.supabase_service_role_key)


async def get_supabase() -> Client:
    """Get regular Supabase client for user operations"""
    return supabase


async def get_supabase_admin() -> Client:
    """Get admin Supabase client for service operations"""
    return supabase_admin


class DatabaseService:
    """Database service for common operations"""
    
    def __init__(self, client: Client = None):
        self.client = client or supabase_admin
    
    async def get_user_profile(self, user_id: str):
        """Get user profile by ID"""
        try:
            response = self.client.table("profiles").select("*").eq("id", user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None
    
    async def get_project(self, project_id: str, user_id: str = None):
        """Get project by ID with access check"""
        try:
            query = self.client.table("projects").select("*").eq("id", project_id)
            
            if user_id:
                # Add access control
                query = query.or_(f"owner_id.eq.{user_id},is_demo.eq.true")
            
            response = query.execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting project: {e}")
            return None
    
    async def get_project_feedbacks(self, project_id: str, limit: int = 50, offset: int = 0):
        """Get feedbacks for a project with pagination"""
        try:
            response = (
                self.client
                .table("feedbacks")
                .select("*, analyses(*)")
                .eq("project_id", project_id)
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Error getting project feedbacks: {e}")
            return []
    
    async def create_feedback(self, feedback_data: dict):
        """Create a new feedback"""
        try:
            response = self.client.table("feedbacks").insert(feedback_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating feedback: {e}")
            return None
    
    async def create_analysis(self, analysis_data: dict):
        """Create or update analysis for a feedback"""
        try:
            # Use upsert to handle updates
            response = (
                self.client
                .table("analyses")
                .upsert(analysis_data, on_conflict="feedback_id")
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating analysis: {e}")
            return None
    
    async def create_orchestrate_job(self, job_data: dict):
        """Create an orchestrate job"""
        try:
            response = self.client.table("orchestrate_jobs").insert(job_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating orchestrate job: {e}")
            return None
    
    async def get_pending_orchestrate_jobs(self, limit: int = 10):
        """Get pending orchestrate jobs for processing"""
        try:
            response = (
                self.client
                .table("orchestrate_jobs")
                .select("*")
                .eq("status", "queued")
                .order("scheduled_at")
                .limit(limit)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Error getting pending orchestrate jobs: {e}")
            return []
    
    async def update_orchestrate_job(self, job_id: str, updates: dict):
        """Update orchestrate job status"""
        try:
            response = (
                self.client
                .table("orchestrate_jobs")
                .update(updates)
                .eq("id", job_id)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error updating orchestrate job: {e}")
            return None
    
    async def log_audit(self, user_id: str, action: str, resource_type: str, 
                       resource_id: str = None, details: dict = None, 
                       ip_address: str = None, user_agent: str = None):
        """Log audit event"""
        try:
            audit_data = {
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "details": details or {},
                "ip_address": ip_address,
                "user_agent": user_agent
            }
            response = self.client.table("audit_logs").insert(audit_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error logging audit: {e}")
            return None
