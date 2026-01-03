from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Use a synchronous driver for Alembic migrations
DATABASE_URL_SYNC = "postgresql+pg8000://postgres:1234@localhost:5432/resume_builder"

engine = create_engine(DATABASE_URL_SYNC, echo=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def get_db_sync():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()