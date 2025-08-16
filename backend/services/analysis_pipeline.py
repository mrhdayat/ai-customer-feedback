import asyncio
import time
import logging
from typing import Dict, Any, List, Optional
from models import (
    Feedback, Analysis, SentimentLabel, UrgencyLevel,
    LanguageDetection, SentimentResult, TopicResult, EntityResult, GraniteResult
)
from services.language_detection import detect_language
from services.huggingface_service import HuggingFaceService
from services.watson_service import WatsonNLUService
from services.replicate_service import ReplicateService
from services.orchestrate_service import (
    OrchestrateService, should_trigger_automation, create_automation_payload
)
from database import DatabaseService

logger = logging.getLogger(__name__)


class AnalysisPipeline:
    """Complete AI analysis pipeline for customer feedback"""
    
    def __init__(self):
        self.hf_service = HuggingFaceService()
        self.watson_service = WatsonNLUService()
        self.replicate_service = ReplicateService()
        self.orchestrate_service = OrchestrateService()
        self.db_service = DatabaseService()
    
    async def analyze_feedback(self, feedback_id: str, force_reanalysis: bool = False) -> Optional[Dict[str, Any]]:
        """
        Run complete analysis pipeline for a single feedback
        """
        start_time = time.time()
        errors = []
        
        try:
            # Get feedback data
            feedback_response = await self.db_service.client.table("feedbacks").select("*").eq("id", feedback_id).execute()
            if not feedback_response.data:
                logger.error(f"Feedback {feedback_id} not found")
                return None
            
            feedback_data = feedback_response.data[0]
            
            # Check if analysis already exists
            if not force_reanalysis:
                existing_analysis = await self.db_service.client.table("analyses").select("*").eq("feedback_id", feedback_id).execute()
                if existing_analysis.data:
                    logger.info(f"Analysis already exists for feedback {feedback_id}")
                    return existing_analysis.data[0]
            
            text = feedback_data["content"]
            language_input = feedback_data.get("language", "auto")
            
            logger.info(f"Starting analysis pipeline for feedback {feedback_id}")
            
            # Step 1: Language Detection
            detected_lang, lang_confidence = detect_language(text) if language_input == "auto" else (language_input, 1.0)
            logger.info(f"Detected language: {detected_lang} (confidence: {lang_confidence:.2f})")
            
            # Step 2: Run AI services in parallel
            sentiment_task = self.hf_service.analyze_sentiment(text, detected_lang)
            topics_task = self.hf_service.classify_topics(text)
            entities_task = self.watson_service.extract_entities(text, detected_lang)
            
            # Wait for parallel tasks
            sentiment_result, topics_result, entities_result = await asyncio.gather(
                sentiment_task, topics_task, entities_task, return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(sentiment_result, Exception):
                errors.append(f"Sentiment analysis failed: {sentiment_result}")
                sentiment_result = SentimentResult(
                    label=SentimentLabel.NEUTRAL, score=0.5, confidence=0.0, model="fallback"
                )
            
            if isinstance(topics_result, Exception):
                errors.append(f"Topic classification failed: {topics_result}")
                topics_result = TopicResult(topics=[], model="fallback", threshold=0.35)
            
            if isinstance(entities_result, Exception):
                errors.append(f"Entity extraction failed: {entities_result}")
                entities_result = EntityResult(entities=[], keywords=[], categories=[], service="fallback")
            
            # Step 3: Granite refinement
            prior_analysis = {
                "language": detected_lang,
                "sentiment": {
                    "label": sentiment_result.label.value,
                    "score": sentiment_result.score,
                    "confidence": sentiment_result.confidence
                },
                "topics": [{"label": t.label, "score": t.score} for t in topics_result.topics],
                "entities": [{"text": e.text, "type": e.type} for e in entities_result.entities]
            }
            
            try:
                granite_result = await self.replicate_service.refine_analysis(text, prior_analysis)
            except Exception as e:
                errors.append(f"Granite analysis failed: {e}")
                granite_result = GraniteResult(
                    summary=f"Customer feedback analysis",
                    topics_fixed=[],
                    tie_break=None,
                    insights={"urgency": UrgencyLevel.LOW, "action_recommendation": "Review manually"},
                    raw_response=""
                )
            
            # Step 4: Build analysis result
            processing_time = int((time.time() - start_time) * 1000)
            
            analysis_data = {
                "feedback_id": feedback_id,
                "detected_language": detected_lang,
                "sentiment_label": sentiment_result.label.value,
                "sentiment_score": sentiment_result.score,
                "sentiment_confidence": sentiment_result.confidence,
                "sentiment_model": sentiment_result.model,
                "topics": [
                    {
                        "label": topic.label,
                        "score": topic.score,
                        "confidence": topic.confidence or topic.score
                    }
                    for topic in topics_result.topics
                ],
                "topics_fixed": [
                    {
                        "label": topic.label,
                        "score": topic.score,
                        "confidence": topic.confidence or topic.score
                    }
                    for topic in granite_result.topics_fixed
                ],
                "entities": [
                    {
                        "text": entity.text,
                        "type": entity.type,
                        "confidence": entity.confidence,
                        "metadata": entity.metadata
                    }
                    for entity in entities_result.entities
                ],
                "keywords": entities_result.keywords,
                "categories": entities_result.categories,
                "granite_summary": granite_result.summary,
                "granite_insights": {
                    "urgency": granite_result.insights.urgency.value,
                    "action_recommendation": granite_result.insights.action_recommendation,
                    "confidence": granite_result.insights.confidence,
                    "reasoning": granite_result.insights.reasoning
                },
                "granite_tie_break": granite_result.tie_break,
                "granite_raw": granite_result.raw_response,
                "processing_time_ms": processing_time,
                "errors": errors
            }
            
            # Step 5: Save analysis
            saved_analysis = await self.db_service.create_analysis(analysis_data)
            
            if not saved_analysis:
                logger.error(f"Failed to save analysis for feedback {feedback_id}")
                return None
            
            # Step 6: Check for automation triggers
            if should_trigger_automation(feedback_data, analysis_data):
                await self._trigger_automation(feedback_data, analysis_data)
            
            logger.info(f"Analysis completed for feedback {feedback_id} in {processing_time}ms")
            return saved_analysis
            
        except Exception as e:
            logger.error(f"Analysis pipeline failed for feedback {feedback_id}: {e}")
            return None
    
    async def analyze_batch(self, feedback_ids: List[str], force_reanalysis: bool = False) -> Dict[str, Any]:
        """
        Run analysis pipeline for multiple feedbacks
        """
        results = {
            "success": [],
            "failed": [],
            "total": len(feedback_ids)
        }
        
        # Process in batches to avoid overwhelming services
        batch_size = 5
        for i in range(0, len(feedback_ids), batch_size):
            batch = feedback_ids[i:i + batch_size]
            
            # Process batch in parallel
            tasks = [self.analyze_feedback(fid, force_reanalysis) for fid in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for feedback_id, result in zip(batch, batch_results):
                if isinstance(result, Exception) or result is None:
                    results["failed"].append({
                        "feedback_id": feedback_id,
                        "error": str(result) if isinstance(result, Exception) else "Unknown error"
                    })
                else:
                    results["success"].append({
                        "feedback_id": feedback_id,
                        "analysis_id": result["id"]
                    })
            
            # Small delay between batches
            if i + batch_size < len(feedback_ids):
                await asyncio.sleep(1)
        
        logger.info(f"Batch analysis completed: {len(results['success'])} success, {len(results['failed'])} failed")
        return results
    
    async def _trigger_automation(self, feedback_data: Dict[str, Any], analysis_data: Dict[str, Any]):
        """
        Trigger automation workflows based on analysis
        """
        try:
            urgency = analysis_data.get("granite_insights", {}).get("urgency", "low")
            
            jobs_to_create = []
            
            # Create ticket for medium/high urgency
            if urgency in ["medium", "high"]:
                ticket_payload = create_automation_payload(feedback_data, analysis_data, "ticket")
                jobs_to_create.append({
                    "feedback_id": feedback_data["id"],
                    "analysis_id": analysis_data.get("id"),
                    "kind": "ticket",
                    "payload": ticket_payload
                })
            
            # Create alert for high urgency
            if urgency == "high":
                alert_payload = create_automation_payload(feedback_data, analysis_data, "alert")
                jobs_to_create.append({
                    "feedback_id": feedback_data["id"],
                    "analysis_id": analysis_data.get("id"),
                    "kind": "alert",
                    "payload": alert_payload
                })
            
            # Save orchestrate jobs
            for job_data in jobs_to_create:
                await self.db_service.create_orchestrate_job(job_data)
                logger.info(f"Created {job_data['kind']} job for feedback {feedback_data['id']}")
                
        except Exception as e:
            logger.error(f"Failed to trigger automation: {e}")


# Worker function for processing orchestrate jobs
async def process_orchestrate_jobs():
    """
    Background worker to process queued orchestrate jobs
    """
    db_service = DatabaseService()
    orchestrate_service = OrchestrateService()
    
    while True:
        try:
            # Get pending jobs
            jobs = await db_service.get_pending_orchestrate_jobs(limit=5)
            
            if not jobs:
                await asyncio.sleep(30)  # Wait 30 seconds if no jobs
                continue
            
            for job in jobs:
                try:
                    # Update job status to processing
                    await db_service.update_orchestrate_job(job["id"], {
                        "status": "processing",
                        "started_at": "NOW()"
                    })
                    
                    # Execute the job
                    if job["kind"] == "ticket":
                        result = await orchestrate_service.create_ticket(
                            {"id": job["feedback_id"]}, 
                            job["payload"]
                        )
                    elif job["kind"] == "alert":
                        result = await orchestrate_service.send_alert(
                            {"id": job["feedback_id"]}, 
                            job["payload"]
                        )
                    else:
                        # Generic workflow/skill execution
                        result = await orchestrate_service.trigger_skill(
                            job["kind"], 
                            job["payload"]
                        )
                    
                    # Update job with result
                    if result.get("success"):
                        await db_service.update_orchestrate_job(job["id"], {
                            "status": "completed",
                            "response": result.get("response", {}),
                            "external_ref": result.get("external_ref"),
                            "completed_at": "NOW()"
                        })
                        logger.info(f"Orchestrate job {job['id']} completed successfully")
                    else:
                        # Handle failure with retry logic
                        retry_count = job["retry_count"] + 1
                        if retry_count <= job["max_retries"]:
                            await db_service.update_orchestrate_job(job["id"], {
                                "status": "queued",
                                "retry_count": retry_count,
                                "error_message": result.get("error", "Unknown error"),
                                "scheduled_at": "NOW() + INTERVAL '5 minutes'"
                            })
                            logger.warning(f"Orchestrate job {job['id']} failed, retrying ({retry_count}/{job['max_retries']})")
                        else:
                            await db_service.update_orchestrate_job(job["id"], {
                                "status": "failed",
                                "retry_count": retry_count,
                                "error_message": result.get("error", "Max retries exceeded"),
                                "completed_at": "NOW()"
                            })
                            logger.error(f"Orchestrate job {job['id']} failed permanently")
                
                except Exception as e:
                    logger.error(f"Error processing orchestrate job {job['id']}: {e}")
                    await db_service.update_orchestrate_job(job["id"], {
                        "status": "failed",
                        "error_message": str(e),
                        "completed_at": "NOW()"
                    })
            
            await asyncio.sleep(10)  # Wait between job batches
            
        except Exception as e:
            logger.error(f"Orchestrate worker error: {e}")
            await asyncio.sleep(60)  # Wait longer on error
