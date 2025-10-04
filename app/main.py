# app/main.py
import logging
from fastapi import FastAPI, Depends, HTTPException, Header, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from typing import List
from .config import settings
from .db import get_db, SessionLocal, engine
from . import models, schemas, crud
from .search_index import search_index
from .ai_service import generate_reply
from fastapi.middleware.cors import CORSMiddleware

# logging
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
logger = logging.getLogger(__name__)

# create DB tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Reviews Copilot — Professional Backend", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # frontend origin
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, OPTIONS, etc.
    allow_headers=["*"],  # includes x-api-key
)

# API key dependency
def get_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.API_KEY.get_secret_value():
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return x_api_key

@app.get("/health")
def health():
    return {"status": "ok", "env": settings.ENV}

@app.post("/ingest", response_model=schemas.IngestResp)
def ingest(reviews: List[schemas.ReviewIn], db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    if not reviews:
        raise HTTPException(status_code=400, detail="Empty payload")
    added, skipped = crud.ingest_reviews(db, reviews)
    return {"ingested": added, "skipped": skipped}

from pydantic import BaseModel
from typing import List

class ReviewsResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[schemas.ReviewOut]

@app.get("/reviews", response_model=ReviewsResponse)
def list_reviews(
    location: str | None = None,
    sentiment: str | None = None,
    q: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    try:
        query = db.query(models.Review)
        if location:
            query = query.filter(func.lower(models.Review.location) == location.lower())
        if sentiment:
            query = query.filter(func.lower(models.Review.sentiment) == sentiment.lower())
        if q:
            query = query.filter(models.Review.text.ilike(f"%{q}%"))
        
        total = query.count()  # total number of filtered reviews
        items = query.order_by(models.Review.date.desc())\
                     .offset((page-1)*page_size)\
                     .limit(page_size)\
                     .all()
        
        return {"total": total, "page": page, "page_size": page_size, "items": items}
    except Exception as e:
        logger.exception("Error fetching reviews")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reviews/{review_id}", response_model=schemas.ReviewOut)
def get_review(review_id: int, db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    r = crud.get_review(db, review_id)
    if not r:
        raise HTTPException(status_code=404, detail="Review not found")
    return r

@app.post("/reviews/{review_id}/suggest-reply", response_model=schemas.SuggestReplyResp)
def suggest_reply(review_id: int, db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    r = crud.get_review(db, review_id)
    if not r:
        raise HTTPException(status_code=404, detail="Review not found")
    reply, tags, log = generate_reply(r.text)
    # persisted tags
    crud.update_tags(db, review_id, tags.get("sentiment"), tags.get("topic"))
    return {"reply": reply, "tags": tags, "reasoning_log": log}

@app.get("/search")
def search(q: str = Query(..., min_length=1), k: int = Query(5, ge=1, le=20), api_key: str = Depends(get_api_key)):
    results = search_index.query(q, top_k=k)
    return {"query": q, "results": [{"id": r[0], "score": r[1]} for r in results]}

@app.get("/analytics", response_model=schemas.AnalyticsResp)
def analytics(db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    sentiment_counts = dict(
        db.query(models.Review.sentiment, func.count(models.Review.id))
          .filter(models.Review.sentiment.isnot(None))
          .group_by(models.Review.sentiment)
          .all()
    )
    topic_counts = dict(
        db.query(models.Review.topic, func.count(models.Review.id))
          .filter(models.Review.topic.isnot(None))
          .group_by(models.Review.topic)
          .all()
    )
    return {"by_sentiment": sentiment_counts, "by_topic": topic_counts}

