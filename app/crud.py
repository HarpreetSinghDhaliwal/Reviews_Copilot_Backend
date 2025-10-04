# app/crud.py
from sqlalchemy.orm import Session
from . import models, schemas
from typing import List, Tuple
from datetime import date
from .search_index import search_index
import logging

logger = logging.getLogger(__name__)

def ingest_reviews(db: Session, reviews: List[schemas.ReviewIn]) -> Tuple[int,int]:
    """Insert new reviews. Returns (added, skipped)"""
    added = 0
    skipped = 0
    to_index = []
    for r in reviews:
        existing = db.query(models.Review).filter_by(id=r.id).first()
        if existing:
            skipped += 1
            continue
        m = models.Review(
            id=r.id, location=r.location, rating=r.rating, text=r.text, date=r.date
        )
        db.add(m)
        added += 1
        to_index.append((r.id, r.text))
    db.commit()
    if to_index:
        # add to in-memory index and rebuild persistently
        search_index.add_bulk(to_index, rebuild=True)
    logger.info("Ingested %d reviews, skipped %d", added, skipped)
    return added, skipped

def get_review(db: Session, review_id: int):
    return db.query(models.Review).filter_by(id=review_id).first()

def update_tags(db: Session, review_id: int, sentiment: str | None, topic: str | None):
    r = db.query(models.Review).filter_by(id=review_id).first()
    if not r:
        return None
    if sentiment:
        r.sentiment = sentiment
    if topic:
        r.topic = topic
    db.add(r)
    db.commit()
    return r
