import httpx
import logging
from typing import Dict, Any, Optional
from config import settings

logger = logging.getLogger(__name__)


class OrchestrateService:
    """Service for IBM Orchestrate automation"""
    
    def __init__(self):
        self.api_key = settings.ibm_orchestrate_api_key
        self.base_url = settings.ibm_orchestrate_base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def trigger_workflow(self, workflow_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trigger an IBM Orchestrate workflow
        """
        try:
            url = f"{self.base_url}/v1/workflows/{workflow_id}/run"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code in [200, 201, 202]:
                    result = response.json()
                    return {
                        "success": True,
                        "response": result,
                        "external_ref": result.get("run_id") or result.get("id"),
                        "status": "submitted"
                    }
                else:
                    logger.error(f"Orchestrate workflow error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"API error: {response.status_code}",
                        "details": response.text
                    }
                    
        except Exception as e:
            logger.error(f"Orchestrate workflow failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def trigger_skill(self, skill_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trigger an IBM Orchestrate skill
        """
        try:
            url = f"{self.base_url}/v1/skills/{skill_id}/run"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code in [200, 201, 202]:
                    result = response.json()
                    return {
                        "success": True,
                        "response": result,
                        "external_ref": result.get("run_id") or result.get("id"),
                        "status": "submitted"
                    }
                else:
                    logger.error(f"Orchestrate skill error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"API error: {response.status_code}",
                        "details": response.text
                    }
                    
        except Exception as e:
            logger.error(f"Orchestrate skill failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_ticket(self, feedback_data: Dict[str, Any], analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a support ticket through Orchestrate
        """
        # Map feedback and analysis to ticket format
        ticket_payload = {
            "title": f"Customer Feedback - {analysis_data.get('sentiment_label', 'Unknown')} Sentiment",
            "description": feedback_data.get("content", ""),
            "priority": self._get_ticket_priority(analysis_data),
            "category": self._get_ticket_category(analysis_data),
            "customer_info": {
                "name": feedback_data.get("author_name"),
                "source": feedback_data.get("source"),
                "url": feedback_data.get("source_url")
            },
            "analysis": {
                "sentiment": analysis_data.get("sentiment_label"),
                "confidence": analysis_data.get("sentiment_confidence"),
                "topics": analysis_data.get("topics", []),
                "urgency": analysis_data.get("granite_insights", {}).get("urgency"),
                "recommendation": analysis_data.get("granite_insights", {}).get("action_recommendation")
            }
        }
        
        # Use a generic ticket creation skill ID
        # In production, this would be configured per organization
        skill_id = "create_support_ticket"
        
        return await self.trigger_skill(skill_id, ticket_payload)
    
    async def send_alert(self, feedback_data: Dict[str, Any], analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send an alert notification through Orchestrate
        """
        alert_payload = {
            "type": "customer_feedback_alert",
            "severity": self._get_alert_severity(analysis_data),
            "message": f"Urgent customer feedback requires attention",
            "details": {
                "feedback_content": feedback_data.get("content", ""),
                "sentiment": analysis_data.get("sentiment_label"),
                "urgency": analysis_data.get("granite_insights", {}).get("urgency"),
                "recommendation": analysis_data.get("granite_insights", {}).get("action_recommendation"),
                "source": feedback_data.get("source"),
                "author": feedback_data.get("author_name")
            },
            "channels": ["slack", "email"]  # Configure notification channels
        }
        
        # Use a generic alert skill ID
        skill_id = "send_alert_notification"
        
        return await self.trigger_skill(skill_id, alert_payload)
    
    def _get_ticket_priority(self, analysis_data: Dict[str, Any]) -> str:
        """Determine ticket priority based on analysis"""
        urgency = analysis_data.get("granite_insights", {}).get("urgency", "low")
        sentiment = analysis_data.get("sentiment_label", "neutral")
        
        if urgency == "high" or sentiment == "negative":
            return "high"
        elif urgency == "medium":
            return "medium"
        else:
            return "low"
    
    def _get_ticket_category(self, analysis_data: Dict[str, Any]) -> str:
        """Determine ticket category based on topics"""
        topics = analysis_data.get("topics", [])
        
        if not topics:
            return "general"
        
        # Get the highest scoring topic
        top_topic = topics[0].get("label", "general") if topics else "general"
        
        category_mapping = {
            "layanan": "customer_service",
            "produk": "product_issue",
            "pengiriman": "delivery",
            "harga": "billing",
            "lokasi": "location",
            "kualitas": "quality",
            "after-sales": "support"
        }
        
        return category_mapping.get(top_topic, "general")
    
    def _get_alert_severity(self, analysis_data: Dict[str, Any]) -> str:
        """Determine alert severity"""
        urgency = analysis_data.get("granite_insights", {}).get("urgency", "low")
        
        if urgency == "high":
            return "critical"
        elif urgency == "medium":
            return "warning"
        else:
            return "info"


# Helper function to determine if feedback should trigger automation
def should_trigger_automation(feedback_data: Dict[str, Any], analysis_data: Dict[str, Any]) -> bool:
    """
    Determine if feedback should trigger automated actions
    """
    sentiment = analysis_data.get("sentiment_label")
    urgency = analysis_data.get("granite_insights", {}).get("urgency", "low")
    topics = analysis_data.get("topics", [])
    entities = analysis_data.get("entities", [])
    
    # Trigger if negative sentiment or medium/high urgency
    if sentiment == "negative" or urgency in ["medium", "high"]:
        # And if topics are related to actionable categories
        actionable_topics = {"layanan", "pengiriman", "kualitas", "after-sales"}
        topic_labels = {topic.get("label", "") for topic in topics}
        
        if actionable_topics.intersection(topic_labels):
            return True
        
        # Or if entities indicate product or location issues
        entity_types = {entity.get("type", "") for entity in entities}
        if {"product", "location", "organization"}.intersection(entity_types):
            return True
    
    return False


def create_automation_payload(feedback_data: Dict[str, Any], analysis_data: Dict[str, Any], kind: str) -> Dict[str, Any]:
    """
    Create payload for automation job
    """
    base_payload = {
        "feedback_id": feedback_data.get("id"),
        "feedback_content": feedback_data.get("content"),
        "source": feedback_data.get("source"),
        "author": feedback_data.get("author_name"),
        "sentiment": analysis_data.get("sentiment_label"),
        "urgency": analysis_data.get("granite_insights", {}).get("urgency"),
        "topics": analysis_data.get("topics", []),
        "recommendation": analysis_data.get("granite_insights", {}).get("action_recommendation")
    }
    
    if kind == "ticket":
        return {
            **base_payload,
            "ticket_type": "customer_feedback",
            "auto_assign": True
        }
    elif kind == "alert":
        return {
            **base_payload,
            "alert_type": "urgent_feedback",
            "channels": ["slack", "email"]
        }
    else:
        return base_payload
