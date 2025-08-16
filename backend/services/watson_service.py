import httpx
import logging
from typing import List, Dict, Any
from config import settings
from models import Entity, EntityResult

logger = logging.getLogger(__name__)


class WatsonNLUService:
    """Service for IBM Watson Natural Language Understanding"""
    
    def __init__(self):
        self.api_key = settings.ibm_watson_nlu_api_key
        self.url = settings.ibm_watson_nlu_url
        self.version = "2022-04-07"
    
    async def extract_entities(self, text: str, language: str = "auto") -> EntityResult:
        """
        Extract entities, keywords, and categories using Watson NLU
        """
        try:
            # Determine language code for Watson
            watson_language = self._get_watson_language_code(language)
            
            url = f"{self.url}/v1/analyze"
            
            payload = {
                "text": text,
                "features": {
                    "entities": {
                        "model": watson_language,
                        "sentiment": True,
                        "emotion": False
                    },
                    "keywords": {
                        "sentiment": True,
                        "emotion": False,
                        "limit": 10
                    },
                    "categories": {
                        "limit": 5
                    }
                },
                "language": watson_language,
                "return_analyzed_text": False
            }
            
            params = {"version": self.version}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    params=params,
                    json=payload,
                    auth=("apikey", self.api_key)
                )
                
                if response.status_code != 200:
                    logger.error(f"Watson NLU API error: {response.status_code} - {response.text}")
                    raise Exception(f"API error: {response.status_code}")
                
                result = response.json()
                
                # Process entities
                entities = []
                if "entities" in result:
                    for entity in result["entities"]:
                        entities.append(Entity(
                            text=entity.get("text", ""),
                            type=entity.get("type", ""),
                            confidence=entity.get("confidence", 0.0),
                            metadata={
                                "count": entity.get("count", 1),
                                "sentiment": entity.get("sentiment", {}),
                                "disambiguation": entity.get("disambiguation", {})
                            }
                        ))
                
                # Process keywords
                keywords = []
                if "keywords" in result:
                    for keyword in result["keywords"]:
                        keywords.append({
                            "text": keyword.get("text", ""),
                            "relevance": keyword.get("relevance", 0.0),
                            "count": keyword.get("count", 1),
                            "sentiment": keyword.get("sentiment", {})
                        })
                
                # Process categories
                categories = []
                if "categories" in result:
                    for category in result["categories"]:
                        categories.append({
                            "label": category.get("label", ""),
                            "score": category.get("score", 0.0)
                        })
                
                return EntityResult(
                    entities=entities,
                    keywords=keywords,
                    categories=categories,
                    service="watson_nlu"
                )
                
        except Exception as e:
            logger.error(f"Watson NLU entity extraction failed: {e}")
            return EntityResult(
                entities=[],
                keywords=[],
                categories=[],
                service="watson_nlu_fallback"
            )
    
    def _get_watson_language_code(self, language: str) -> str:
        """Convert language code to Watson NLU format"""
        # Watson NLU supported languages
        watson_languages = {
            "en": "en",
            "es": "es",
            "fr": "fr",
            "de": "de",
            "it": "it",
            "pt": "pt",
            "ru": "ru",
            "ja": "ja",
            "ko": "ko",
            "zh": "zh",
            "ar": "ar"
        }
        
        # For Indonesian and other unsupported languages, fall back to English
        if language in watson_languages:
            return watson_languages[language]
        else:
            return "en"  # Default to English for unsupported languages
