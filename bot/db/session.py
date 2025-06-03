from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from bot.core.config import DATABASE_URL
from bot.db.models import Base # Important for Alembic and table creation

engine = create_engine(DATABASE_URL) # Add connect_args for SQLite if needed e.g. {"check_same_thread": False} for web apps

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_db_and_tables():
    # This is for initial creation if not using Alembic, or for tests.
    # Alembic is the preferred way to manage schema.
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
