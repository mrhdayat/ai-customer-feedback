from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any
import logging
from models import (
    ProjectCreate, ProjectUpdate, Project, ProjectSummary,
    APIResponse, PaginatedResponse, Feedback
)
from auth import get_optional_user, require_member_or_admin, require_admin
from database import DatabaseService
from middleware import limiter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("/", response_model=APIResponse)
async def get_projects(
    current_user: Optional[dict] = Depends(get_optional_user),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50)
):
    """Get user's projects (including demo projects for unauthenticated users)"""
    try:
        db_service = DatabaseService()
        offset = (page - 1) * per_page
        
        if current_user:
            # Authenticated user - get their projects + demo projects
            if current_user.get("role") == "admin":
                # Admin sees all projects
                response = await db_service.client.table("projects").select(
                    "*"
                ).order("created_at", desc=True).range(offset, offset + per_page - 1).execute()
            else:
                # Member sees their own projects + demo projects
                response = await db_service.client.table("projects").select(
                    "*"
                ).or_(f"owner_id.eq.{current_user['id']},is_demo.eq.true").order(
                    "created_at", desc=True
                ).range(offset, offset + per_page - 1).execute()
        else:
            # Unauthenticated user - only demo projects
            response = await db_service.client.table("projects").select(
                "*"
            ).eq("is_demo", True).order("created_at", desc=True).range(
                offset, offset + per_page - 1
            ).execute()
        
        # Get total count for pagination
        count_response = await db_service.client.table("projects").select(
            "*", count="exact"
        ).execute()
        total = count_response.count
        
        return APIResponse(
            success=True,
            message="Projects retrieved successfully",
            data={
                "projects": response.data,
                "pagination": {
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": (total + per_page - 1) // per_page
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting projects: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=APIResponse)
@limiter.limit("10/minute")
async def create_project(
    request,
    project: ProjectCreate,
    current_user: dict = Depends(require_member_or_admin)
):
    """Create a new project"""
    try:
        db_service = DatabaseService()
        
        project_data = {
            **project.dict(),
            "owner_id": current_user["id"],
            "is_demo": False
        }
        
        created_project = await db_service.client.table("projects").insert(project_data).execute()
        
        if not created_project.data:
            raise HTTPException(status_code=500, detail="Failed to create project")
        
        # Log audit
        await db_service.log_audit(
            user_id=current_user["id"],
            action="create_project",
            resource_type="project",
            resource_id=created_project.data[0]["id"],
            details={"name": project.name}
        )
        
        return APIResponse(
            success=True,
            message="Project created successfully",
            data=created_project.data[0]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{project_id}", response_model=APIResponse)
async def get_project(
    project_id: str,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """Get a single project"""
    try:
        db_service = DatabaseService()
        
        project = await db_service.get_project(project_id, current_user["id"] if current_user else None)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return APIResponse(
            success=True,
            message="Project retrieved successfully",
            data=project
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{project_id}", response_model=APIResponse)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    current_user: dict = Depends(require_member_or_admin)
):
    """Update a project"""
    try:
        db_service = DatabaseService()
        
        # Check project access
        project = await db_service.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Only owner or admin can update
        if project["owner_id"] != current_user["id"] and current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Update project
        update_data = {k: v for k, v in project_update.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        response = await db_service.client.table("projects").update(update_data).eq(
            "id", project_id
        ).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to update project")
        
        # Log audit
        await db_service.log_audit(
            user_id=current_user["id"],
            action="update_project",
            resource_type="project",
            resource_id=project_id,
            details=update_data
        )
        
        return APIResponse(
            success=True,
            message="Project updated successfully",
            data=response.data[0]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating project: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{project_id}", response_model=APIResponse)
async def delete_project(
    project_id: str,
    current_user: dict = Depends(require_member_or_admin)
):
    """Delete a project"""
    try:
        db_service = DatabaseService()
        
        # Check project access
        project = await db_service.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Only owner or admin can delete
        if project["owner_id"] != current_user["id"] and current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Prevent deletion of demo projects
        if project["is_demo"]:
            raise HTTPException(status_code=400, detail="Cannot delete demo projects")
        
        # Delete project (cascades to feedbacks, analyses, jobs)
        await db_service.client.table("projects").delete().eq("id", project_id).execute()
        
        # Log audit
        await db_service.log_audit(
            user_id=current_user["id"],
            action="delete_project",
            resource_type="project",
            resource_id=project_id,
            details={"name": project["name"]}
        )
        
        return APIResponse(
            success=True,
            message="Project deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{project_id}/feedbacks", response_model=APIResponse)
async def get_project_feedbacks(
    project_id: str,
    current_user: Optional[dict] = Depends(get_optional_user),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    source: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    topic: Optional[str] = Query(None)
):
    """Get feedbacks for a project with filtering and pagination"""
    try:
        db_service = DatabaseService()
        
        # Check project access
        project = await db_service.get_project(project_id, current_user["id"] if current_user else None)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        offset = (page - 1) * per_page
        
        # Build query
        query = db_service.client.table("feedbacks").select(
            "*, analyses(*)"
        ).eq("project_id", project_id)
        
        # Apply filters
        if source:
            query = query.eq("source", source)
        
        if sentiment:
            # Filter by analysis sentiment
            query = query.not_.is_("analyses", "null").eq("analyses.sentiment_label", sentiment)
        
        if topic:
            # Filter by topic (this is more complex, might need a different approach in production)
            query = query.not_.is_("analyses", "null").like("analyses.topics", f'%"{topic}"%')
        
        # Execute query with pagination
        response = query.order("created_at", desc=True).range(offset, offset + per_page - 1).execute()
        
        # Get total count
        count_query = db_service.client.table("feedbacks").select("*", count="exact").eq("project_id", project_id)
        if source:
            count_query = count_query.eq("source", source)
        count_response = count_query.execute()
        total = count_response.count
        
        return APIResponse(
            success=True,
            message="Feedbacks retrieved successfully",
            data={
                "feedbacks": response.data,
                "pagination": {
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": (total + per_page - 1) // per_page
                },
                "filters": {
                    "source": source,
                    "sentiment": sentiment,
                    "topic": topic
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project feedbacks: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{project_id}/summary", response_model=APIResponse)
async def get_project_summary(
    project_id: str,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """Get project analytics summary"""
    try:
        db_service = DatabaseService()
        
        # Check project access
        project = await db_service.get_project(project_id, current_user["id"] if current_user else None)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get total feedbacks
        total_response = await db_service.client.table("feedbacks").select(
            "*", count="exact"
        ).eq("project_id", project_id).execute()
        total_feedbacks = total_response.count
        
        # Get sentiment distribution
        sentiment_response = await db_service.client.table("analyses").select(
            "sentiment_label"
        ).in_(
            "feedback_id", 
            [f["id"] for f in (await db_service.client.table("feedbacks").select("id").eq("project_id", project_id).execute()).data]
        ).execute()
        
        sentiment_distribution = {}
        for analysis in sentiment_response.data:
            sentiment = analysis.get("sentiment_label", "unknown")
            sentiment_distribution[sentiment] = sentiment_distribution.get(sentiment, 0) + 1
        
        # Get top topics (simplified - in production you'd aggregate properly)
        topics_response = await db_service.client.table("analyses").select(
            "topics"
        ).in_(
            "feedback_id",
            [f["id"] for f in (await db_service.client.table("feedbacks").select("id").eq("project_id", project_id).execute()).data]
        ).execute()
        
        topic_counts = {}
        for analysis in topics_response.data:
            topics = analysis.get("topics", [])
            for topic in topics:
                label = topic.get("label", "unknown")
                topic_counts[label] = topic_counts.get(label, 0) + 1
        
        top_topics = [
            {"label": label, "count": count}
            for label, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        # Get urgency distribution
        urgency_response = await db_service.client.table("analyses").select(
            "granite_insights"
        ).in_(
            "feedback_id",
            [f["id"] for f in (await db_service.client.table("feedbacks").select("id").eq("project_id", project_id).execute()).data]
        ).execute()
        
        urgency_distribution = {}
        for analysis in urgency_response.data:
            insights = analysis.get("granite_insights", {})
            urgency = insights.get("urgency", "unknown")
            urgency_distribution[urgency] = urgency_distribution.get(urgency, 0) + 1
        
        # Get automation stats
        automation_response = await db_service.client.table("orchestrate_jobs").select(
            "status"
        ).in_(
            "feedback_id",
            [f["id"] for f in (await db_service.client.table("feedbacks").select("id").eq("project_id", project_id).execute()).data]
        ).execute()
        
        automation_stats = {}
        for job in automation_response.data:
            status = job.get("status", "unknown")
            automation_stats[status] = automation_stats.get(status, 0) + 1
        
        summary = {
            "total_feedbacks": total_feedbacks,
            "sentiment_distribution": sentiment_distribution,
            "top_topics": top_topics,
            "urgency_distribution": urgency_distribution,
            "automation_stats": automation_stats,
            "recent_trends": []  # Could add time-based trending analysis
        }
        
        return APIResponse(
            success=True,
            message="Project summary retrieved successfully",
            data=summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
