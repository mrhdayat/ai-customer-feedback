import httpx
import logging
from typing import List, Dict, Any, Optional
from config import settings
from models import SentimentResult, TopicResult, TopicScore, SentimentLabel
from services.language_detection import get_sentiment_model_for_language

logger = logging.getLogger(__name__)


class HuggingFaceService:
    """Service for HuggingFace Inference API"""
    
    def __init__(self):
        self.api_token = settings.huggingface_api_token
        self.base_url = "https://api-inference.huggingface.co/models"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
    
    async def analyze_sentiment(self, text: str, language: str = "auto") -> SentimentResult:
        """
        Analyze sentiment using appropriate model based on language
        """
        try:
            model = get_sentiment_model_for_language(language)
            url = f"{self.base_url}/{model}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json={"inputs": text}
                )
                
                if response.status_code != 200:
                    logger.error(f"HuggingFace sentiment API error: {response.status_code} - {response.text}")
                    raise Exception(f"API error: {response.status_code}")
                
                result = response.json()
                
                # Handle different response formats
                if isinstance(result, list) and len(result) > 0:
                    scores = result[0]
                elif isinstance(result, dict) and "scores" in result:
                    scores = result["scores"]
                else:
                    scores = result
                
                # Find highest scoring sentiment
                if isinstance(scores, list):
                    best_score = max(scores, key=lambda x: x["score"])
                    label = self._normalize_sentiment_label(best_score["label"])
                    score = best_score["score"]
                else:
                    # Fallback for unexpected format
                    label = SentimentLabel.NEUTRAL
                    score = 0.5
                
                return SentimentResult(
                    label=label,
                    score=score,
                    confidence=score,
                    model=model
                )
                
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            # Return neutral sentiment as fallback
            return SentimentResult(
                label=SentimentLabel.NEUTRAL,
                score=0.5,
                confidence=0.0,
                model="fallback"
            )
    
    async def classify_topics(self, text: str, threshold: float = 0.35) -> TopicResult:
        """
        Classify topics using zero-shot classification
        """
        try:
            model = "facebook/bart-large-mnli"
            url = f"{self.base_url}/{model}"
            
            # Define topic categories in Indonesian and English
            candidate_labels = [
                "harga", "price", "pricing",
                "layanan", "service", "customer service",
                "produk", "product", "quality",
                "pengiriman", "delivery", "shipping",
                "lokasi", "location", "place",
                "kualitas", "quality", "quality control",
                "after-sales", "support", "technical support"
            ]
            
            payload = {
                "inputs": text,
                "parameters": {
                    "candidate_labels": candidate_labels,
                    "multi_label": True
                }
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code != 200:
                    logger.error(f"HuggingFace topic API error: {response.status_code} - {response.text}")
                    raise Exception(f"API error: {response.status_code}")
                
                result = response.json()
                
                # Process results
                topics = []
                if "labels" in result and "scores" in result:
                    for label, score in zip(result["labels"], result["scores"]):
                        if score >= threshold:
                            # Normalize topic labels
                            normalized_label = self._normalize_topic_label(label)
                            topics.append(TopicScore(
                                label=normalized_label,
                                score=score,
                                confidence=score
                            ))
                
                # Sort by score descending
                topics.sort(key=lambda x: x.score, reverse=True)
                
                return TopicResult(
                    topics=topics,
                    model=model,
                    threshold=threshold
                )
                
        except Exception as e:
            logger.error(f"Topic classification failed: {e}")
            return TopicResult(
                topics=[],
                model="fallback",
                threshold=threshold
            )
    
    def _normalize_sentiment_label(self, label: str) -> SentimentLabel:
        """Normalize sentiment labels from different models"""
        label_lower = label.lower()
        
        if label_lower in ["positive", "pos", "1"]:
            return SentimentLabel.POSITIVE
        elif label_lower in ["negative", "neg", "0"]:
            return SentimentLabel.NEGATIVE
        else:
            return SentimentLabel.NEUTRAL
    
    def _normalize_topic_label(self, label: str) -> str:
        """Normalize topic labels to consistent categories"""
        label_lower = label.lower()
        
        # Price-related
        if any(word in label_lower for word in ["harga", "price", "pricing"]):
            return "harga"
        
        # Service-related
        elif any(word in label_lower for word in ["layanan", "service"]):
            return "layanan"
        
        # Product-related
        elif any(word in label_lower for word in ["produk", "product"]):
            return "produk"
        
        # Delivery-related
        elif any(word in label_lower for word in ["pengiriman", "delivery", "shipping"]):
            return "pengiriman"
        
        # Location-related
        elif any(word in label_lower for word in ["lokasi", "location", "place"]):
            return "lokasi"
        
        # Quality-related
        elif any(word in label_lower for word in ["kualitas", "quality"]):
            return "kualitas"
        
        # After-sales/Support
        elif any(word in label_lower for word in ["after-sales", "support"]):
            return "after-sales"
        
        else:
            return label_lower
