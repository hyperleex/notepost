import pytest
import datetime
import sqlite3 # Add this import
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession

from bot.database import Post, PostStatus, add_post, get_post, update_post_status, get_pending_posts, Base

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def engine():
    # Explicitly pass detect_types to potentially improve SQLite type handling
    return create_engine(
        TEST_DATABASE_URL,
        connect_args={'detect_types': sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES}
    )

@pytest.fixture(scope="function")
def tables(engine):
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(engine, tables):
    connection = engine.connect()
    transaction = connection.begin()
    session = SQLAlchemySession(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

def test_create_post(db_session: SQLAlchemySession):
    user_id = 123
    text = "Test post content"
    publish_at_dt = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
    created_post = add_post(db_session, user_id=user_id, text=text, publish_at=publish_at_dt)
    assert created_post is not None
    assert created_post.id is not None
    assert created_post.user_id == user_id
    assert created_post.text == text
    assert created_post.status == PostStatus.PENDING
    assert created_post.publish_at is not None
    # For SQLite, DateTime(timezone=True) stores as naive UTC, retrieves as naive.
    # Let's ensure the original timezone-aware datetime, when converted to naive UTC, matches.
    expected_publish_at_naive_utc = publish_at_dt.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    assert created_post.publish_at == expected_publish_at_naive_utc, \
        "publish_at (naive) should match original dt converted to naive UTC"
    assert created_post.created_at is not None

def test_get_post(db_session: SQLAlchemySession):
    user_id = 456
    text = "Another test post"
    created_post = add_post(db_session, user_id=user_id, text=text)
    retrieved_post = get_post(db_session, created_post.id)
    assert retrieved_post is not None
    assert retrieved_post.id == created_post.id
    assert retrieved_post.text == text

def test_get_pending_posts(db_session: SQLAlchemySession):
    now = datetime.datetime.now(datetime.timezone.utc)
    add_post(db_session, user_id=1, text="Pending post 1", publish_at=now)
    published_post = add_post(db_session, user_id=2, text="Published post 1")
    update_post_status(db_session, published_post.id, PostStatus.PUBLISHED)
    add_post(db_session, user_id=3, text="Pending post 2", publish_at=now + datetime.timedelta(hours=1))
    pending_posts = get_pending_posts(db_session)
    assert len(pending_posts) == 2
    for p in pending_posts:
        assert p.status == PostStatus.PENDING
    if len(pending_posts) == 2:
        assert pending_posts[0].user_id == 1
        assert pending_posts[1].user_id == 3

def test_update_post_status(db_session: SQLAlchemySession):
    user_id = 789
    text = "Post to be updated"
    created_post = add_post(db_session, user_id=user_id, text=text)
    updated = update_post_status(db_session, created_post.id, PostStatus.PUBLISHED)
    assert updated is True
    updated_post = get_post(db_session, created_post.id)
    assert updated_post is not None
    assert updated_post.status == PostStatus.PUBLISHED
    assert updated_post.updated_at is not None

def test_get_non_existent_post(db_session: SQLAlchemySession):
    retrieved_post = get_post(db_session, 99999)
    assert retrieved_post is None

def test_update_non_existent_post_status(db_session: SQLAlchemySession):
    updated = update_post_status(db_session, 99999, PostStatus.PUBLISHED)
    assert updated is False
