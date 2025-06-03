from sqlalchemy.orm import Session
from typing import List, Optional

from .models import Admin, Channel, Post, Media, Poll, Watermark, Autosign, Template # Import all models
import datetime
from .models import PostStatusEnum, ContentTypeEnum # Import enums if needed for filtering
import datetime

# Admin CRUD operations
def create_admin(db: Session, admin_id: int, first_name: Optional[str] = None, username: Optional[str] = None) -> Admin:
    db_admin = Admin(admin_id=admin_id, first_name=first_name, username=username)
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    return db_admin

def get_admin(db: Session, admin_id: int) -> Optional[Admin]:
    return db.query(Admin).filter(Admin.admin_id == admin_id).first()

def get_admins(db: Session, skip: int = 0, limit: int = 100) -> List[Admin]:
    return db.query(Admin).offset(skip).limit(limit).all()

def update_admin_activity(db: Session, admin_id: int, is_active: bool) -> Optional[Admin]:
    db_admin = get_admin(db, admin_id)
    if db_admin:
        db_admin.is_active = is_active
        db.commit()
        db.refresh(db_admin)
    return db_admin

# Channel CRUD operations
def create_channel(db: Session, channel_id: int, admin_id: int, title: Optional[str] = None, username: Optional[str] = None) -> Channel:
    # Ensure admin exists
    admin = get_admin(db, admin_id)
    if not admin:
        # Or raise an exception, depending on how you want to handle this
        raise ValueError(f"Admin with id {admin_id} not found.")

    db_channel = Channel(channel_id=channel_id, admin_id=admin_id, title=title, username=username, is_connected=True)
    db.add(db_channel)
    db.commit()
    db.refresh(db_channel)
    return db_channel

def get_channel(db: Session, channel_id: int) -> Optional[Channel]:
    return db.query(Channel).filter(Channel.channel_id == channel_id).first()

def get_channels_by_admin(db: Session, admin_id: int, skip: int = 0, limit: int = 50) -> List[Channel]:
    # Max 50 channels per bot, but an admin might have fewer.
    return db.query(Channel).filter(Channel.admin_id == admin_id, Channel.is_connected == True).offset(skip).limit(limit).all()

def update_channel_connectivity(db: Session, channel_id: int, is_connected: bool) -> Optional[Channel]:
    db_channel = get_channel(db, channel_id)
    if db_channel:
        db_channel.is_connected = is_connected
        db.commit()
        db.refresh(db_channel)
    return db_channel

# Post CRUD operations (Example stubs, to be expanded)
def create_post(db: Session, channel_id: int, admin_id: int, content_type: ContentTypeEnum, text_content: Optional[str] = None, publish_at: Optional[datetime.datetime] = None, status: PostStatusEnum = PostStatusEnum.DRAFT) -> Post:
    # Simplified, more fields to be added based on Post model
    db_post = Post(
        channel_id=channel_id,
        admin_id=admin_id,
        content_type=content_type,
        text_content=text_content,
        publish_at=publish_at,
        status=status
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

def get_post(db: Session, post_id: int) -> Optional[Post]:
    return db.query(Post).filter(Post.post_id == post_id).first()

def get_posts_by_channel(db: Session, channel_id: int, skip: int = 0, limit: int = 100) -> List[Post]:
    return db.query(Post).filter(Post.channel_id == channel_id).order_by(Post.created_at.desc()).offset(skip).limit(limit).all()

def get_posts_by_status(db: Session, status: PostStatusEnum, skip: int = 0, limit: int = 100) -> List[Post]:
    return db.query(Post).filter(Post.status == status).order_by(Post.publish_at.asc()).offset(skip).limit(limit).all()

def update_post_status(db: Session, post_id: int, new_status: PostStatusEnum, error_message: Optional[str] = None) -> Optional[Post]:
    db_post = get_post(db, post_id)
    if db_post:
        db_post.status = new_status
        if error_message:
            db_post.error_message = error_message
        db.commit()
        db.refresh(db_post)
    return db_post

# Add more CRUD functions for Media, Poll, Watermark, Autosign, Template later.
# For example:
# def create_media_item(db: Session, file_id: str, file_unique_id: str, media_type: str, uploader_admin_id: int, file_size_bytes: Optional[int] = None) -> Media:
#     # ... implementation ...
#     pass

# def get_active_watermark_for_admin(db: Session, admin_id: int) -> Optional[Watermark]:
#     # ... implementation ...
#     pass

# def get_active_autosign_for_admin(db: Session, admin_id: int) -> Optional[Autosign]:
#     # ... implementation ...
#     pass

# Make sure to import datetime if used (e.g. for publish_at type hint in create_post)
# Add 'import datetime' at the top of the file.
