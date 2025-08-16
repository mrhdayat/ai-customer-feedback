from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
import logging
from models import (
    FeedbackCreate, Feedback, AnalysisRequest, AnalysisBatchRequest,
    APIResponse, PaginatedResponse
)
from auth import get_optional_user, require_member_or_admin
from database import DatabaseService
from services.analysis_pipeline import AnalysisPipeline
from middleware import limiter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/feedbacks", tags=["feedbacks"])


@router.post("/", response_model=APIResponse)
@limiter.limit("10/minute")
async def create_feedback(
    request,
    project_id: str,
    feedback: FeedbackCreate,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """Create a new feedback"""
    try:
        db_service = DatabaseService()
        
        # Check project access
        project = await db_service.get_project(project_id, current_user["id"] if current_user else None)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Demo users can't create feedbacks
        if not current_user or current_user.get("role") == "demo_viewer":
            raise HTTPException(
                status_code=403, 
                detail="Demo users cannot create feedbacks. Please sign up for a member account."
            )
        
        # Create feedback
        feedback_data = {
            **feedback.dict(),
            "project_id": project_id
        }
        
        created_feedback = await db_service.create_feedback(feedback_data)
        if not created_feedback:
            raise HTTPException(status_code=500, detail="Failed to create feedback")
        
        # Log audit
        await db_service.log_audit(
            user_id=current_user["id"],
            action="create_feedback",
            resource_type="feedback",
            resource_id=created_feedback["id"],
            details={"project_id": project_id}
        )
        
        return APIResponse(
            success=True,
            message="Feedback created successfully",
            data=created_feedback
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating feedback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/batch", response_model=APIResponse)
@limiter.limit("5/minute")
async def create_feedback_batch(
    request,
    project_id: str,
    feedbacks: List[FeedbackCreate],
    current_user: dict = Depends(require_member_or_admin)
):
    """Create multiple feedbacks in batch"""
    try:
        if len(feedbacks) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 feedbacks per batch")
        
        db_service = DatabaseService()
        
        # Check project access
        project = await db_service.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        created_feedbacks = []
        errors = []
        
        for i, feedback in enumerate(feedbacks):
            try:
                feedback_data = {
                    **feedback.dict(),
                    "project_id": project_id
                }
                
                created = await db_service.create_feedback(feedback_data)
                if created:
                    created_feedbacks.append(created)
                else:
                    errors.append(f"Row {i+1}: Failed to create feedback")
            except Exception as e:
                errors.append(f"Row {i+1}: {str(e)}")
        
        # Log audit
        await db_service.log_audit(
            user_id=current_user["id"],
            action="create_feedback_batch",
            resource_type="feedback",
            details={
                "project_id": project_id,
                "total": len(feedbacks),
                "success": len(created_feedbacks),
                "errors": len(errors)
            }
        )
        
        return APIResponse(
            success=len(errors) == 0,
            message=f"Created {len(created_feedbacks)} feedbacks" + (f", {len(errors)} errors" if errors else ""),
            data={
                "created": created_feedbacks,
                "errors": errors
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating feedback batch: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{feedback_id}", response_model=APIResponse)
async def get_feedback(
    feedback_id: str,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """Get a single feedback with analysis"""
    try:
        db_service = DatabaseService()
        
        # Get feedback with analysis
        response = await db_service.client.table("feedbacks").select(
            "*, analyses(*)"
        ).eq("id", feedback_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Feedback not found")
        
        feedback = response.data[0]
        
        # Check project access
        project = await db_service.get_project(feedback["project_id"], current_user["id"] if current_user else None)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return APIResponse(
            success=True,
            message="Feedback retrieved successfully",
            data=feedback
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feedback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{feedback_id}/analyze", response_model=APIResponse)
@limiter.limit("20/minute")
async def analyze_feedback(
    request,
    feedback_id: str,
    analysis_request: AnalysisRequest,
    current_user: dict = Depends(require_member_or_admin)
):
    """Analyze a single feedback"""
    try:
        db_service = DatabaseService()
        pipeline = AnalysisPipeline()
        
        # Verify feedback exists and user has access
        feedback_response = await db_service.client.table("feedbacks").select(
            "*, project_id"
        ).eq("id", feedback_id).execute()
        
        if not feedback_response.data:
            raise HTTPException(status_code=404, detail="Feedback not found")
        
        feedback = feedback_response.data[0]
        project = await db_service.get_project(feedback["project_id"], current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Run analysis
        analysis_result = await pipeline.analyze_feedback(
            feedback_id, 
            force_reanalysis=analysis_request.force_reanalysis
        )
        
        if not analysis_result:
            raise HTTPException(status_code=500, detail="Analysis failed")
        
        # Log audit
        await db_service.log_audit(
            user_id=current_user["id"],
            action="analyze_feedback",
            resource_type="feedback",
            resource_id=feedback_id,
            details={"force_reanalysis": analysis_request.force_reanalysis}
        )
        
        return APIResponse(
            success=True,
            message="Analysis completed successfully",
            data=analysis_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing feedback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/analyze/batch", response_model=APIResponse)
@limiter.limit("10/minute")
async def analyze_feedback_batch(
    request,
    batch_request: AnalysisBatchRequest,
    current_user: dict = Depends(require_member_or_admin)
):
    """Analyze multiple feedbacks in batch"""
    try:
        if len(batch_request.feedback_ids) > 20:
            raise HTTPException(status_code=400, detail="Maximum 20 feedbacks per batch")
        
        pipeline = AnalysisPipeline()
        
        # Run batch analysis
        results = await pipeline.analyze_batch(
            batch_request.feedback_ids,
            force_reanalysis=batch_request.force_reanalysis
        )
        
        # Log audit
        db_service = DatabaseService()
        await db_service.log_audit(
            user_id=current_user["id"],
            action="analyze_feedback_batch",
            resource_type="feedback",
            details={
                "total": len(batch_request.feedback_ids),
                "success": len(results["success"]),
                "failed": len(results["failed"])
            }
        )
        
        return APIResponse(
            success=len(results["failed"]) == 0,
            message=f"Analyzed {len(results['success'])} feedbacks" + (f", {len(results['failed'])} failed" if results["failed"] else ""),
            data=results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing feedback batch: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{feedback_id}", response_model=APIResponse)
async def delete_feedback(
    feedback_id: str,
    current_user: dict = Depends(require_member_or_admin)
):
    """Delete a feedback"""
    try:
        db_service = DatabaseService()
        
        # Verify feedback exists and user has access
        feedback_response = await db_service.client.table("feedbacks").select(
            "*, project_id"
        ).eq("id", feedback_id).execute()
        
        if not feedback_response.data:
            raise HTTPException(status_code=404, detail="Feedback not found")
        
        feedback = feedback_response.data[0]
        project = await db_service.get_project(feedback["project_id"], current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Delete feedback (cascades to analysis and jobs)
        await db_service.client.table("feedbacks").delete().eq("id", feedback_id).execute()
        
        # Log audit
        await db_service.log_audit(
            user_id=current_user["id"],
            action="delete_feedback",
            resource_type="feedback",
            resource_id=feedback_id,
            details={"project_id": feedback["project_id"]}
        )
        
        return APIResponse(
            success=True,
            message="Feedback deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting feedback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
