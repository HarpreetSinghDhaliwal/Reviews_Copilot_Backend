import re
import os
import json
import logging
import google.generativeai as genai
from typing import Tuple, Dict, List
from .config import settings

logger = logging.getLogger(__name__)

# Lazy import transformers when used
_transformers = None


def _redact(text: str) -> str:
    r = text
    if settings.REDACT_EMAIL:
        r = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', '[REDACTED_EMAIL]', r)
    if settings.REDACT_PHONE:
        r = re.sub(r'(\+?\d[\d\-\s]{6,}\d)', '[REDACTED_PHONE]', r)
    return r


def _profanity_check(text: str) -> bool:
    banned = {"idiot", "stupid", "dumb"}
    t = text.lower()
    return any(word in t for word in banned)


def local_reply_pipeline(text: str) -> Tuple[str, Dict[str, str], List[str]]:
    global _transformers
    try:
        from transformers import pipeline
    except Exception as e:
        logger.exception("transformers not installed or failed: %s", e)
        red = _redact(text)
        return (
            "Thanks for your feedback. We're sorry you had a bad experience — we'll look into this.",
            {"sentiment": "unknown", "topic": "general"},
            [f"redacted: {red}"]
        )

    if _transformers is None:
        _transformers = {
            "sentiment": pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english"),
            "summ": pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
        }

    redacted = _redact(text)
    if _profanity_check(redacted):
        logger.warning("Input contains potential profanity.")
        redacted = re.sub(r'\b\w+\b', '[REDACTED]', redacted)

    s = _transformers["sentiment"](redacted)[0]
    sentiment = s.get("label", "NEUTRAL")

    summary = _transformers["summ"](redacted, max_length=15, min_length=5, do_sample=False)[0]["summary_text"]

    low = redacted.lower()
    topic = "service" if any(w in low for w in ("service", "staff", "wait", "attend", "checkout")) else \
        "product" if any(w in low for w in ("quality", "item", "taste", "broken", "missing")) else \
        "price" if "price" in low or "expensive" in low else "general"

    reply = f"Hi — thank you for your feedback. {summary} We're sorry about this and will follow up to improve our {topic}."
    reasoning = [
        f"redacted_text: {redacted}",
        f"sentiment: {sentiment}",
        f"summary: {summary}",
        f"topic: {topic}"
    ]
    return reply, {"sentiment": sentiment, "topic": topic}, reasoning


def generate_reply(text: str, project: int = 1) -> Tuple[str, Dict[str, str], List[str]]:
    """
    Generate a reply. Tries Gemini first, then falls back to local pipeline.
    """

    # 1. Try Gemini if key is available
    if settings.GEMINI_API_KEY:
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)

            gemini_model = settings.GEMINI_MODEL_ID if settings.GEMINI_MODEL_ID else "gemini-1.5-flash"

            prompt = f"""
You are an assistant for generating customer service replies.
Analyze the following review text and return JSON with:
- reply: short, empathetic reply
- sentiment: POSITIVE, NEUTRAL, or NEGATIVE
- topic: service, product, price, or general
Return only JSON.

Review:
\"\"\"{text}\"\"\"
"""

            model = genai.GenerativeModel(gemini_model)
            response = model.generate_content(
                prompt,
                generation_config={
                    "response_mime_type": "application/json"
                }
            )

            content = response.text.strip()
            data = json.loads(content)

            reply = data.get("reply", "")
            tags = {
                "sentiment": data.get("sentiment", "UNKNOWN"),
                "topic": data.get("topic", "general")
            }
            reasoning_log = [f"Used Gemini API. Original: {text}"]
            logger.info("Successfully generated reply using Gemini.")
            return reply, tags, reasoning_log

        except Exception as e:
            logger.warning("Gemini call failed (%s). Falling back to local pipeline.", e)

    # 2. Fallback to Local Pipeline
    logger.info("No Gemini API key available or call failed. Using local pipeline.")
    return local_reply_pipeline(text)
