from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any
import logging
from models import APIResponse, OrchestrateJob, JobStatus
from auth import require_member_or_admin, require_admin
from database import DatabaseService
from services.orchestrate_service import OrchestrateService
from middleware import limiter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/orchestrate", tags=["orchestrate"])


@router.get("/jobs", response_model=APIResponse)
async def get_orchestrate_jobs(
    current_user: dict = Depends(require_member_or_admin),
    project_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """Get orchestrate jobs for user's projects"""
    try:
        db_service = DatabaseService()
        offset = (page - 1) * per_page
        
        # Build query
        query = db_service.client.table("orchestrate_jobs").select(
            "*, feedbacks!inner(project_id, content), analyses!inner(*)"
        )
        
        # Filter by project if specified
        if project_id:
            # Check project access
            project = await db_service.get_project(project_id, current_user["id"])
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            query = query.eq("feedbacks.project_id", project_id)
        else:
            # Filter to user's projects only (unless admin)
            if current_user.get("role") != "admin":
                query = query.eq("feedbacks.project_id.owner_id", current_user["id"])
        
        # Filter by status if specified
        if status_filter:
            query = query.eq("status", status_filter)
        
        # Execute query
        response = query.order("created_at", desc=True).range(offset, offset + per_page - 1).execute()
        
        # Get total count
        count_query = db_service.client.table("orchestrate_jobs").select("*", count="exact")
        if project_id:
            count_query = count_query.eq("feedbacks.project_id", project_id)
        if status_filter:
            count_query = count_query.eq("status", status_filter)
        count_response = count_query.execute()
        total = count_response.count
        
        return APIResponse(
            success=True,
            message="Orchestrate jobs retrieved successfully",
            data={
                "jobs": response.data,
                "pagination": {
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": (total + per_page - 1) // per_page
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting orchestrate jobs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/jobs/{job_id}/retry", response_model=APIResponse)
@limiter.limit("10/minute")
async def retry_orchestrate_job(
    request,
    job_id: str,
    current_user: dict = Depends(require_member_or_admin)
):
    """Retry a failed orchestrate job"""
    try:
        db_service = DatabaseService()
        
        # Get job and verify access
        job_response = await db_service.client.table("orchestrate_jobs").select(
            "*, feedbacks!inner(project_id)"
        ).eq("id", job_id).execute()
        
        if not job_response.data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = job_response.data[0]
        
        # Check project access
        project_id = job["feedbacks"]["project_id"]
        project = await db_service.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Check if job can be retried
        if job["status"] not in ["failed", "cancelled"]:
            raise HTTPException(status_code=400, detail="Job cannot be retried")
        
        if job["retry_count"] >= job["max_retries"]:
            raise HTTPException(status_code=400, detail="Max retries exceeded")
        
        # Reset job for retry
        update_data = {
            "status": "queued",
            "retry_count": job["retry_count"] + 1,
            "error_message": None,
            "scheduled_at": "NOW()"
        }
        
        await db_service.update_orchestrate_job(job_id, update_data)
        
        # Log audit
        await db_service.log_audit(
            user_id=current_user["id"],
            action="retry_orchestrate_job",
            resource_type="orchestrate_job",
            resource_id=job_id,
            details={"kind": job["kind"]}
        )
        
        return APIResponse(
            success=True,
            message="Job queued for retry"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying orchestrate job: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/jobs/{job_id}/cancel", response_model=APIResponse)
async def cancel_orchestrate_job(
    job_id: str,
    current_user: dict = Depends(require_member_or_admin)
):
    """Cancel a queued orchestrate job"""
    try:
        db_service = DatabaseService()
        
        # Get job and verify access
        job_response = await db_service.client.table("orchestrate_jobs").select(
            "*, feedbacks!inner(project_id)"
        ).eq("id", job_id).execute()
        
        if not job_response.data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = job_response.data[0]
        
        # Check project access
        project_id = job["feedbacks"]["project_id"]
        project = await db_service.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Check if job can be cancelled
        if job["status"] not in ["queued", "processing"]:
            raise HTTPException(status_code=400, detail="Job cannot be cancelled")
        
        # Cancel job
        await db_service.update_orchestrate_job(job_id, {
            "status": "cancelled",
            "completed_at": "NOW()"
        })
        
        # Log audit
        await db_service.log_audit(
            user_id=current_user["id"],
            action="cancel_orchestrate_job",
            resource_type="orchestrate_job",
            resource_id=job_id,
            details={"kind": job["kind"]}
        )
        
        return APIResponse(
            success=True,
            message="Job cancelled successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling orchestrate job: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/trigger/{feedback_id}", response_model=APIResponse)
@limiter.limit("20/minute")
async def trigger_manual_orchestrate(
    request,
    feedback_id: str,
    job_kind: str,
    current_user: dict = Depends(require_member_or_admin)
):
    """Manually trigger orchestrate job for a feedback"""
    try:
        db_service = DatabaseService()
        
        # Get feedback and analysis
        feedback_response = await db_service.client.table("feedbacks").select(
            "*, analyses(*)"
        ).eq("id", feedback_id).execute()
        
        if not feedback_response.data:
            raise HTTPException(status_code=404, detail="Feedback not found")
        
        feedback = feedback_response.data[0]
        analysis = feedback.get("analyses", [{}])[0] if feedback.get("analyses") else {}
        
        if not analysis:
            raise HTTPException(status_code=400, detail="Feedback has not been analyzed yet")
        
        # Check project access
        project = await db_service.get_project(feedback["project_id"], current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Create orchestrate job
        from services.orchestrate_service import create_automation_payload
        
        payload = create_automation_payload(feedback, analysis, job_kind)
        
        job_data = {
            "feedback_id": feedback_id,
            "analysis_id": analysis["id"],
            "kind": job_kind,
            "payload": payload
        }
        
        created_job = await db_service.create_orchestrate_job(job_data)
        
        if not created_job:
            raise HTTPException(status_code=500, detail="Failed to create orchestrate job")
        
        # Log audit
        await db_service.log_audit(
            user_id=current_user["id"],
            action="trigger_manual_orchestrate",
            resource_type="orchestrate_job",
            resource_id=created_job["id"],
            details={"feedback_id": feedback_id, "kind": job_kind}
        )
        
        return APIResponse(
            success=True,
            message=f"Orchestrate job ({job_kind}) created successfully",
            data=created_job
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering manual orchestrate: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/skills", response_model=APIResponse)
async def get_available_skills(current_user: dict = Depends(require_admin)):
    """Get available orchestrate skills (admin only)"""
    try:
        # In production, this would query IBM Orchestrate API for available skills
        # For demo, return static list
        skills = [
            {
                "id": "create_support_ticket",
                "name": "Create Support Ticket",
                "description": "Create a support ticket in the ticketing system",
                "parameters": ["title", "description", "priority", "category"]
            },
            {
                "id": "send_alert_notification",
                "name": "Send Alert Notification",
                "description": "Send alert to Slack/Email channels",
                "parameters": ["message", "severity", "channels"]
            },
            {
                "id": "assign_to_team",
                "name": "Assign to Team",
                "description": "Assign feedback to appropriate team",
                "parameters": ["team", "feedback_data", "urgency"]
            },
            {
                "id": "schedule_followup",
                "name": "Schedule Follow-up",
                "description": "Schedule follow-up action or call",
                "parameters": ["customer_info", "schedule_date", "action_type"]
            }
        ]
        
        return APIResponse(
            success=True,
            message="Available skills retrieved",
            data=skills
        )
        
    except Exception as e:
        logger.error(f"Error getting available skills: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
