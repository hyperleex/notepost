import enum
import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Text,
    Enum as SQLAlchemyEnum, JSON
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func # For server_default=func.now()

# Using the DATABASE_URL from config for the Base connection (though Base itself doesn't connect)
# from bot.core.config import DATABASE_URL # Not strictly needed for model definition but good for context

Base = declarative_base()

# Enum definitions (Python enums)
class ContentTypeEnum(str, enum.Enum):
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"
    DOCUMENT = "document"
    ALBUM = "album"
    POLL = "poll"
    VIDEO_NOTE = "video_note"

class PostStatusEnum(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval" # If a review process is ever needed
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing" # Intermediate state while sending
    PUBLISHED = "published"
    FAILED_TO_PUBLISH = "failed_to_publish"
    CANCELLED = "cancelled"
    AUTO_DELETED = "auto_deleted" # After successful auto-deletion

class MediaTypeEnum(str, enum.Enum):
    PHOTO = "photo"
    VIDEO = "video"
    DOCUMENT = "document"
    VIDEO_NOTE = "video_note"
    WATERMARK_PNG = "watermark_png" # Specific type for watermark images

class WatermarkPositionEnum(str, enum.Enum):
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"
    CENTER = "center"
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"

# Models
class Admin(Base):
    __tablename__ = "admins"
    admin_id = Column(Integer, primary_key=True, index=True) # Telegram User ID
    first_name = Column(String(255), nullable=True)
    username = Column(String(255), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    channels = relationship("Channel", back_populates="admin")
    posts = relationship("Post", back_populates="admin")
    media_uploads = relationship("Media", back_populates="uploader")
    watermarks = relationship("Watermark", back_populates="admin")
    autosigns = relationship("Autosign", back_populates="admin")
    templates = relationship("Template", back_populates="admin")

class Channel(Base):
    __tablename__ = "channels"
    channel_id = Column(Integer, primary_key=True, index=True) # Telegram Channel ID (use BigInteger if they can be > 2^31-1)
    admin_id = Column(Integer, ForeignKey("admins.admin_id"), nullable=False)
    title = Column(String(255), nullable=True)
    username = Column(String(255), nullable=True, index=True)
    is_connected = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    admin = relationship("Admin", back_populates="channels")
    posts = relationship("Post", back_populates="channel")

class Post(Base):
    __tablename__ = "posts"
    post_id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(Integer, ForeignKey("channels.channel_id"), nullable=False, index=True)
    admin_id = Column(Integer, ForeignKey("admins.admin_id"), nullable=False, index=True)

    content_type = Column(SQLAlchemyEnum(ContentTypeEnum), nullable=False)
    text_content = Column(Text, nullable=True) # For Markdown/HTML

    status = Column(SQLAlchemyEnum(PostStatusEnum), default=PostStatusEnum.DRAFT, nullable=False, index=True)
    publish_at = Column(DateTime(timezone=True), nullable=True, index=True) # Aware datetime

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now()) # server_default for initial creation

    auto_delete_after_hours = Column(Integer, nullable=True)
    is_pinned_on_publish = Column(Boolean, default=False)

    watermark_id = Column(Integer, ForeignKey("watermarks.watermark_id"), nullable=True)
    autosign_id = Column(Integer, ForeignKey("autosigns.autosign_id"), nullable=True)

    error_message = Column(Text, nullable=True) # For failed posts

    admin = relationship("Admin", back_populates="posts")
    channel = relationship("Channel", back_populates="posts")
    album_media_items = relationship("AlbumMediaItem", back_populates="post", cascade="all, delete-orphan")
    poll = relationship("Poll", back_populates="post", uselist=False, cascade="all, delete-orphan") # One-to-one with Post for poll data
    # Relationships to active watermark/autosign at time of scheduling/publishing might be tricky if they change.
    # Storing IDs is fine, implies "use this specific one".
    active_watermark = relationship("Watermark") # To fetch the chosen watermark
    active_autosign = relationship("Autosign") # To fetch the chosen autosign

class Media(Base):
    __tablename__ = "media"
    file_id = Column(String(255), primary_key=True) # Telegram file_id
    file_unique_id = Column(String(255), unique=True, nullable=False, index=True)
    media_type = Column(SQLAlchemyEnum(MediaTypeEnum), nullable=False)
    uploader_admin_id = Column(Integer, ForeignKey("admins.admin_id"), nullable=False)
    file_size_bytes = Column(Integer, nullable=True) # Store file size if available
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    uploader = relationship("Admin", back_populates="media_uploads")

class AlbumMediaItem(Base):
    __tablename__ = "album_media_items"
    item_id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.post_id"), nullable=False) # Part of a specific post
    media_file_id = Column(String, ForeignKey("media.file_id"), nullable=False) # The actual media
    item_order = Column(Integer, nullable=False) # Order in the album (0-indexed)

    post = relationship("Post", back_populates="album_media_items")
    media_item = relationship("Media") # To get details of the media

class Poll(Base):
    __tablename__ = "polls"
    poll_id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.post_id"), nullable=False, unique=True) # Each post can have at most one poll
    question = Column(String(255), nullable=False) # Telegram limit: 1-300 characters for question
    options_json = Column(JSON, nullable=False) # Store list of options as JSON: [{"text": "Option 1"}, {"text": "Option 2"}] (Telegram: 1-100 chars per option, 2-10 options)
    is_anonymous = Column(Boolean, default=True)
    allows_multiple_answers = Column(Boolean, default=False)
    # 'allows_vote_change' is not a direct Poll parameter in Bot API, but a quiz setting.
    # For regular polls, votes are usually final by default unless the poll is stopped and restarted.
    # We'll stick to standard poll parameters.
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    post = relationship("Post", back_populates="poll")

class Watermark(Base):
    __tablename__ = "watermarks"
    watermark_id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(Integer, ForeignKey("admins.admin_id"), nullable=False)
    media_file_id = Column(String, ForeignKey("media.file_id"), nullable=False) # The watermark image (PNG)
    position = Column(SQLAlchemyEnum(WatermarkPositionEnum), default=WatermarkPositionEnum.BOTTOM_RIGHT)
    name = Column(String(100), nullable=True) # User-friendly name for the watermark
    is_active = Column(Boolean, default=True) # If this is the currently active one for the admin
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    admin = relationship("Admin", back_populates="watermarks")
    media = relationship("Media") # The watermark image itself

class Autosign(Base):
    __tablename__ = "autosigns"
    autosign_id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(Integer, ForeignKey("admins.admin_id"), nullable=False)
    name = Column(String(100), nullable=True) # User-friendly name for the signature
    signature_text = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True) # If this is the currently active one for the admin
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    admin = relationship("Admin", back_populates="autosigns")

class Template(Base):
    __tablename__ = "templates"
    template_id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(Integer, ForeignKey("admins.admin_id"), nullable=False)
    name = Column(String(100), nullable=False) # User-friendly name, unique per admin

    content_type = Column(SQLAlchemyEnum(ContentTypeEnum), nullable=False)
    text_content = Column(Text, nullable=True)
    # For media/album/poll, store structured data.
    # Example: media_json could be {"file_id": "some_id", "caption": "optional"}
    # or for album: {"media": [{"file_id": "id1"}, {"file_id": "id2"}], "caption": "album_caption"}
    media_json = Column(JSON, nullable=True)
    poll_json = Column(JSON, nullable=True) # Similar to Poll.options_json but for defining a template poll

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    admin = relationship("Admin", back_populates="templates")

    __table_args__ = (
        # Unique constraint for template name per admin
        # Removed for now, as SQLite might have issues with multi-column unique through SA if not careful
        # Consider application-level check or a more specific index.
        # UniqueConstraint('admin_id', 'name', name='uq_admin_template_name'),
    )

# Example of how to get engine and create tables (will be in a different file like db_setup.py or session.py)
# def get_engine_example():
#     from bot.core.config import DATABASE_URL
#     return create_engine(DATABASE_URL)

# def create_tables_example(engine):
#     Base.metadata.create_all(bind=engine)
