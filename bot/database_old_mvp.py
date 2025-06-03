import datetime
import enum # Add this import
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Enum as SQLAlchemyEnum
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import func # For server_default=func.now()

DATABASE_URL = "sqlite:///./telegram_poster.db" # Default, can be overridden by config

Base = declarative_base()

class PostStatus(str, enum.Enum): # Changed SQLAlchemyEnum to enum.Enum
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed" # For posts that failed to publish

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    text = Column(String, nullable=False)
    status = Column(SQLAlchemyEnum(PostStatus), nullable=False, default=PostStatus.PENDING, index=True)
    publish_at = Column(DateTime(timezone=True), nullable=True, index=True) # Nullable for immediate or if scheduling is handled differently

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Post(id={self.id}, user_id={self.user_id}, status='{self.status}', publish_at='{self.publish_at}')>"

def get_engine(db_url: str = DATABASE_URL):
    return create_engine(db_url)

def create_db_and_tables(engine):
    # This function is more for initial setup or tests if not using Alembic for table creation directly.
    # Alembic will be the primary tool for managing schema.
    Base.metadata.create_all(bind=engine)

# SessionLocal will be used to create database sessions
Engine = get_engine() # Global engine instance for simplicity in this module
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=Engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Placeholder for actual database operations, which will be added later
def add_post(db_session, user_id: int, text: str, publish_at: datetime.datetime = None) -> Post:
    new_post = Post(user_id=user_id, text=text, publish_at=publish_at, status=PostStatus.PENDING)
    db_session.add(new_post)
    db_session.commit()
    db_session.refresh(new_post)
    return new_post

def get_post(db_session, post_id: int) -> Post | None:
    return db_session.query(Post).filter(Post.id == post_id).first()

def get_pending_posts(db_session) -> list[Post]:
    return db_session.query(Post).filter(Post.status == PostStatus.PENDING).order_by(Post.publish_at.asc()).all()

def update_post_status(db_session, post_id: int, new_status: PostStatus) -> bool:
    post = db_session.query(Post).filter(Post.id == post_id).first()
    if post:
        post.status = new_status
        # If using onupdate for updated_at, it might not trigger automatically here
        # depending on SQLAlchemy version and configuration.
        # Explicitly setting it is safer if there are concerns.
        post.updated_at = func.now() # Explicitly set updated_at for SQLite compatibility with onupdate
        db_session.commit()
        return True
    return False
