# app/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import date

class ReviewIn(BaseModel):
    id: int
    location: str
    rating: int = Field(..., ge=1, le=5)
    text: str
    date: date

class ReviewOut(ReviewIn):
    sentiment: Optional[str] = None
    topic: Optional[str] = None
    class Config:
        from_attributes = True

class IngestResp(BaseModel):
    ingested: int
    skipped: int

class SuggestReplyResp(BaseModel):
    reply: str
    tags: Dict[str, str]
    reasoning_log: List[str]

class AnalyticsResp(BaseModel):
    by_sentiment: Dict[str, int]
    by_topic: Dict[str, int]