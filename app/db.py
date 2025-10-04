# app/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from .config import settings

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {})
SessionLocal = scoped_session(sessionmaker(bind=engine, autocommit=False, autoflush=False))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
