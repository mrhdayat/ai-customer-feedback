import replicate
import json
import logging
from typing import Dict, Any, List, Optional
from config import settings
from models import GraniteResult, GraniteInsights, TopicScore, UrgencyLevel, SentimentLabel

logger = logging.getLogger(__name__)


class ReplicateService:
    """Service for Replicate AI (IBM Granite 3.3-8B Instruct)"""
    
    def __init__(self):
        self.api_token = settings.replicate_api_token
        replicate.Client(api_token=self.api_token)
        self.model = "ibm-granite/granite-3.3-8b-instruct"
    
    async def refine_analysis(self, text: str, prior_analysis: Dict[str, Any]) -> GraniteResult:
        """
        Use Granite to refine analysis, provide summary, and generate insights
        """
        try:
            prompt = self._build_prompt(text, prior_analysis)
            
            # Run Granite model
            output = replicate.run(
                self.model,
                input={
                    "prompt": prompt,
                    "max_new_tokens": 1000,
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "repetition_penalty": 1.1
                }
            )
            
            # Join output if it's a list of strings
            if isinstance(output, list):
                response_text = "".join(output)
            else:
                response_text = str(output)
            
            # Parse JSON response
            parsed_result = self._parse_granite_response(response_text)
            
            if parsed_result:
                return GraniteResult(
                    summary=parsed_result.get("summary", ""),
                    topics_fixed=self._parse_topics_fixed(parsed_result.get("topics_fixed", [])),
                    tie_break=parsed_result.get("tie_break"),
                    insights=self._parse_insights(parsed_result.get("insights", {})),
                    raw_response=response_text
                )
            else:
                # Fallback if JSON parsing fails
                return self._create_fallback_result(text, prior_analysis, response_text)
                
        except Exception as e:
            logger.error(f"Granite analysis failed: {e}")
            return self._create_fallback_result(text, prior_analysis, str(e))
    
    def _build_prompt(self, text: str, prior_analysis: Dict[str, Any]) -> str:
        """Build prompt for Granite model"""
        
        sentiment = prior_analysis.get("sentiment", {})
        topics = prior_analysis.get("topics", [])
        entities = prior_analysis.get("entities", [])
        language = prior_analysis.get("language", "auto")
        
        prompt = f"""You are an expert customer feedback analyst. Analyze the following customer feedback and provide insights in JSON format.

Customer Feedback:
"{text}"

Previous Analysis:
- Language: {language}
- Sentiment: {sentiment.get('label', 'unknown')} (confidence: {sentiment.get('confidence', 0):.2f})
- Topics: {[t.get('label', '') for t in topics[:3]]}
- Key Entities: {[e.get('text', '') for e in entities[:3]]}

Please provide your analysis in the following JSON format:

{{
    "summary": "Brief summary of the feedback in 1-2 sentences",
    "topics_fixed": [
        {{"label": "normalized_topic", "score": 0.85, "confidence": 0.9}}
    ],
    "tie_break": {{"needed": false, "reasoning": "explanation if sentiment confidence was low"}},
    "insights": {{
        "urgency": "low|medium|high",
        "action_recommendation": "Specific actionable recommendation",
        "confidence": 0.85,
        "reasoning": "Why this urgency and action is recommended"
    }}
}}

Guidelines:
- Normalize topics to: harga, layanan, produk, pengiriman, lokasi, kualitas, after-sales
- Urgency levels: low (positive feedback, minor issues), medium (constructive criticism), high (serious complaints, service failures)
- Action recommendations should be specific and actionable
- Use tie_break only if original sentiment confidence < 0.6
- Respond in the same language as the feedback when possible

JSON Response:"""
        
        return prompt
    
    def _parse_granite_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse JSON response from Granite"""
        try:
            # Try to find JSON in the response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            
            return None
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Granite JSON response: {e}")
            return None
    
    def _parse_topics_fixed(self, topics_data: List[Dict]) -> List[TopicScore]:
        """Parse and validate topics from Granite response"""
        topics = []
        for topic in topics_data:
            if isinstance(topic, dict) and "label" in topic and "score" in topic:
                topics.append(TopicScore(
                    label=topic["label"],
                    score=float(topic["score"]),
                    confidence=float(topic.get("confidence", topic["score"]))
                ))
        return topics
    
    def _parse_insights(self, insights_data: Dict) -> GraniteInsights:
        """Parse insights from Granite response"""
        try:
            urgency_str = insights_data.get("urgency", "low").lower()
            if urgency_str == "high":
                urgency = UrgencyLevel.HIGH
            elif urgency_str == "medium":
                urgency = UrgencyLevel.MEDIUM
            else:
                urgency = UrgencyLevel.LOW
            
            return GraniteInsights(
                urgency=urgency,
                action_recommendation=insights_data.get("action_recommendation", "No specific action required"),
                confidence=float(insights_data.get("confidence", 0.7)),
                reasoning=insights_data.get("reasoning", "")
            )
        except Exception as e:
            logger.warning(f"Failed to parse insights: {e}")
            return GraniteInsights(
                urgency=UrgencyLevel.LOW,
                action_recommendation="Review feedback manually",
                confidence=0.5,
                reasoning="Failed to parse AI insights"
            )
    
    def _create_fallback_result(self, text: str, prior_analysis: Dict[str, Any], raw_response: str) -> GraniteResult:
        """Create fallback result when Granite analysis fails"""
        
        # Simple heuristic-based analysis
        sentiment = prior_analysis.get("sentiment", {})
        sentiment_label = sentiment.get("label", "neutral")
        
        # Determine urgency based on sentiment and keywords
        if sentiment_label == "negative":
            urgency = UrgencyLevel.HIGH
            action = "Address customer concerns immediately"
        elif sentiment_label == "positive":
            urgency = UrgencyLevel.LOW
            action = "Maintain current service quality"
        else:
            urgency = UrgencyLevel.MEDIUM
            action = "Monitor for trends and improvements"
        
        # Create basic summary
        text_preview = text[:100] + "..." if len(text) > 100 else text
        summary = f"Customer feedback: {text_preview}"
        
        return GraniteResult(
            summary=summary,
            topics_fixed=[],
            tie_break=None,
            insights=GraniteInsights(
                urgency=urgency,
                action_recommendation=action,
                confidence=0.5,
                reasoning="Fallback analysis due to AI service failure"
            ),
            raw_response=raw_response
        )
