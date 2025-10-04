# app/models.py
from sqlalchemy import Column, Integer, String, Date, Text, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    location = Column(String(128), index=True)
    rating = Column(Integer)
    text = Column(Text)
    date = Column(Date)
    sentiment = Column(String(32), nullable=True, index=True)
    topic = Column(String(64), nullable=True, index=True)

Index("ix_reviews_location_date", Review.location, Review.date)
