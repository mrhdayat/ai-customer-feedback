import langdetect
import langid
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def detect_language(text: str) -> Tuple[str, float]:
    """
    Detect language of text using multiple methods for reliability.
    Returns (language_code, confidence)
    """
    if not text or len(text.strip()) < 3:
        return "auto", 0.0
    
    try:
        # Method 1: langdetect (more accurate for longer texts)
        lang1 = langdetect.detect(text)
        
        # Method 2: langid (more robust)
        lang2, confidence2 = langid.classify(text)
        
        # Normalize common language codes
        lang1 = normalize_language_code(lang1)
        lang2 = normalize_language_code(lang2)
        
        # If both methods agree, return with high confidence
        if lang1 == lang2:
            return lang1, min(0.95, confidence2 + 0.1)
        
        # If they disagree, prefer the one with higher confidence
        # langdetect doesn't provide confidence, so we'll use langid's result
        if confidence2 > 0.7:
            return lang2, confidence2
        else:
            # Fall back to langdetect for short texts where langid might struggle
            return lang1, 0.6
            
    except Exception as e:
        logger.warning(f"Language detection failed: {e}")
        return "auto", 0.0


def normalize_language_code(lang_code: str) -> str:
    """Normalize language codes to common standards"""
    mapping = {
        "id": "id",  # Indonesian
        "en": "en",  # English
        "es": "es",  # Spanish
        "fr": "fr",  # French
        "de": "de",  # German
        "pt": "pt",  # Portuguese
        "it": "it",  # Italian
        "nl": "nl",  # Dutch
        "ru": "ru",  # Russian
        "ja": "ja",  # Japanese
        "ko": "ko",  # Korean
        "zh": "zh",  # Chinese
        "ar": "ar",  # Arabic
        "hi": "hi",  # Hindi
        "th": "th",  # Thai
        "vi": "vi",  # Vietnamese
        "ms": "ms",  # Malay
        "tl": "tl",  # Tagalog
    }
    
    return mapping.get(lang_code.lower(), lang_code.lower())


def get_sentiment_model_for_language(language: str) -> str:
    """Get the appropriate sentiment model for a given language"""
    # Use multilingual model for Indonesian and other non-English languages
    if language in ["id", "es", "fr", "de", "pt", "it", "nl", "ru", "ja", "ko", "zh", "ar", "hi", "th", "vi", "ms", "tl"]:
        return "cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual"
    elif language == "en":
        # For English, we can use either the multilingual or English-specific model
        return "distilbert-base-uncased-finetuned-sst-2-english"
    else:
        # Default to multilingual for unknown languages
        return "cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual"


def should_use_multilingual_model(language: str) -> bool:
    """Check if we should use multilingual model for this language"""
    return language != "en"
