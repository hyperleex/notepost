import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession
from typing import Generator
import datetime

# Assuming your models and Base are in bot.db.models
from bot.db.models import Base, Admin, Channel, Post, PostStatusEnum, ContentTypeEnum
# Assuming your CRUD functions are in bot.db.crud
import bot.db.crud as crud
# Import session utilities - not strictly needed here if we redefine engine for tests,
# but good to be aware of its existence.
# from bot.db.session import SessionLocal as AppSessionLocal, engine as app_engine

# In-memory SQLite database URL for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

# Test engine fixture
@pytest.fixture(scope="session")
def engine():
    # Using a separate engine for tests to ensure isolation from any app-level engine state
    return create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})

# Test tables fixture - creates and drops tables once per session
@pytest.fixture(scope="session")
def tables(engine):
    Base.metadata.create_all(bind=engine) # Create tables
    yield
    Base.metadata.drop_all(bind=engine) # Drop tables

# Test db_session fixture - provides a clean session for each test function
@pytest.fixture(scope="function")
def db_session(engine, tables) -> Generator[SQLAlchemySession, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = SQLAlchemySession(bind=connection)

    yield session

    session.close()
    transaction.rollback() # Rollback any changes made during the test
    connection.close()

# Admin CRUD Tests
def test_create_and_get_admin(db_session: SQLAlchemySession):
    admin_id = 12345
    username = "testadmin"
    created_admin = crud.create_admin(db_session, admin_id=admin_id, username=username, first_name="Test")

    assert created_admin is not None
    assert created_admin.admin_id == admin_id
    assert created_admin.username == username
    assert created_admin.first_name == "Test"
    assert created_admin.is_active is True

    retrieved_admin = crud.get_admin(db_session, admin_id=admin_id)
    assert retrieved_admin is not None
    assert retrieved_admin.admin_id == admin_id

    non_existent_admin = crud.get_admin(db_session, 0)
    assert non_existent_admin is None

def test_get_admins(db_session: SQLAlchemySession):
    crud.create_admin(db_session, admin_id=1, username="admin1")
    crud.create_admin(db_session, admin_id=2, username="admin2")

    admins_limit_1 = crud.get_admins(db_session, limit=1)
    assert len(admins_limit_1) == 1

    all_admins = crud.get_admins(db_session)
    # Check if the created admins are in the list
    admin_ids_in_response = {admin.admin_id for admin in all_admins}
    assert 1 in admin_ids_in_response
    assert 2 in admin_ids_in_response
    # The exact count can be >=2 due to test isolation (rollback) but previous items should be gone.
    # If tests run in parallel or if session scope for tables is an issue, this might need adjustment.
    # For function-scoped rollback, this should be exactly 2 if no other admins were created in this test.
    # Let's refine: create fresh admins and expect exactly those.
    db_session.query(Admin).delete() # Clear previous admins for this specific test if needed, though rollback should handle it.
    db_session.commit()
    crud.create_admin(db_session, admin_id=10, username="admin10")
    crud.create_admin(db_session, admin_id=11, username="admin11")
    current_admins = crud.get_admins(db_session)
    assert len(current_admins) == 2


def test_update_admin_activity(db_session: SQLAlchemySession):
    admin_id = 54321
    crud.create_admin(db_session, admin_id=admin_id)

    updated_admin = crud.update_admin_activity(db_session, admin_id=admin_id, is_active=False)
    assert updated_admin is not None
    assert updated_admin.is_active is False

    retrieved_admin = crud.get_admin(db_session, admin_id=admin_id)
    assert retrieved_admin is not None
    assert retrieved_admin.is_active is False

# Channel CRUD Tests
def test_create_and_get_channel(db_session: SQLAlchemySession):
    admin_id = 98765
    crud.create_admin(db_session, admin_id=admin_id, username="channelowner")

    channel_id = -1001234567890
    channel_username = "testchannel"
    created_channel = crud.create_channel(db_session, channel_id=channel_id, admin_id=admin_id, username=channel_username, title="Test Channel")

    assert created_channel is not None
    assert created_channel.channel_id == channel_id
    assert created_channel.admin_id == admin_id

    retrieved_channel = crud.get_channel(db_session, channel_id=channel_id)
    assert retrieved_channel is not None
    assert retrieved_channel.channel_id == channel_id

def test_create_channel_for_non_existent_admin(db_session: SQLAlchemySession):
    with pytest.raises(ValueError, match="Admin with id 999999 not found"):
        crud.create_channel(db_session, channel_id=-100999, admin_id=999999)

def test_get_channels_by_admin(db_session: SQLAlchemySession):
    admin_id_1 = 111
    admin_id_2 = 222
    crud.create_admin(db_session, admin_id=admin_id_1)
    crud.create_admin(db_session, admin_id=admin_id_2)

    crud.create_channel(db_session, channel_id=-1001, admin_id=admin_id_1, title="Channel 1 Admin 1")
    crud.create_channel(db_session, channel_id=-1002, admin_id=admin_id_1, title="Channel 2 Admin 1")
    crud.create_channel(db_session, channel_id=-1003, admin_id=admin_id_2, title="Channel 1 Admin 2")

    ch_disconnected = crud.create_channel(db_session, channel_id=-1004, admin_id=admin_id_1, title="Disconnected Channel")
    crud.update_channel_connectivity(db_session, ch_disconnected.channel_id, is_connected=False)

    admin1_channels = crud.get_channels_by_admin(db_session, admin_id=admin_id_1)
    assert len(admin1_channels) == 2 # Only connected channels
    for ch in admin1_channels:
        assert ch.admin_id == admin_id_1
        assert ch.is_connected is True

    admin2_channels = crud.get_channels_by_admin(db_session, admin_id=admin_id_2)
    assert len(admin2_channels) == 1

    no_channels_admin = crud.get_channels_by_admin(db_session, admin_id=333)
    assert len(no_channels_admin) == 0

def test_update_channel_connectivity(db_session: SQLAlchemySession):
    admin_id = 888
    crud.create_admin(db_session, admin_id=admin_id)
    channel_id = -2001
    crud.create_channel(db_session, channel_id=channel_id, admin_id=admin_id)

    updated_channel = crud.update_channel_connectivity(db_session, channel_id=channel_id, is_connected=False)
    assert updated_channel is not None
    assert updated_channel.is_connected is False

    retrieved_channel = crud.get_channel(db_session, channel_id=channel_id)
    assert retrieved_channel is not None
    assert retrieved_channel.is_connected is False

# TODO: Add tests for Post CRUD functions (as per plan)

# Post CRUD Tests
def test_create_and_get_post(db_session: SQLAlchemySession):
    admin = crud.create_admin(db_session, admin_id=101, username="postcreator")
    channel = crud.create_channel(db_session, channel_id=-10101, admin_id=admin.admin_id, title="Post Channel")

    post_text = "This is a test post."
    publish_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)

    created_post = crud.create_post(
        db_session,
        channel_id=channel.channel_id,
        admin_id=admin.admin_id,
        content_type=ContentTypeEnum.TEXT,
        text_content=post_text,
        publish_at=publish_time,
        status=PostStatusEnum.SCHEDULED
    )

    assert created_post is not None
    assert created_post.post_id is not None
    assert created_post.channel_id == channel.channel_id
    assert created_post.admin_id == admin.admin_id
    assert created_post.content_type == ContentTypeEnum.TEXT
    assert created_post.text_content == post_text
    # For SQLite, DateTime(timezone=True) stores as naive UTC, retrieves as naive.
    # Compare naive UTC representations.
    expected_publish_at_naive_utc = publish_time.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    assert created_post.publish_at == expected_publish_at_naive_utc
    assert created_post.status == PostStatusEnum.SCHEDULED

    retrieved_post = crud.get_post(db_session, created_post.post_id)
    assert retrieved_post is not None
    assert retrieved_post.text_content == post_text

def test_get_posts_by_channel(db_session: SQLAlchemySession):
    admin = crud.create_admin(db_session, admin_id=102)
    channel1 = crud.create_channel(db_session, channel_id=-10201, admin_id=admin.admin_id)
    channel2 = crud.create_channel(db_session, channel_id=-10202, admin_id=admin.admin_id)

    crud.create_post(db_session, channel_id=channel1.channel_id, admin_id=admin.admin_id, content_type=ContentTypeEnum.TEXT, text_content="Post 1 C1")
    crud.create_post(db_session, channel_id=channel1.channel_id, admin_id=admin.admin_id, content_type=ContentTypeEnum.TEXT, text_content="Post 2 C1")
    crud.create_post(db_session, channel_id=channel2.channel_id, admin_id=admin.admin_id, content_type=ContentTypeEnum.TEXT, text_content="Post 1 C2")

    channel1_posts = crud.get_posts_by_channel(db_session, channel_id=channel1.channel_id)
    assert len(channel1_posts) == 2

    channel2_posts = crud.get_posts_by_channel(db_session, channel_id=channel2.channel_id)
    assert len(channel2_posts) == 1

def test_get_posts_by_status(db_session: SQLAlchemySession):
    admin = crud.create_admin(db_session, admin_id=103)
    channel = crud.create_channel(db_session, channel_id=-10301, admin_id=admin.admin_id)

    crud.create_post(db_session, channel_id=channel.channel_id, admin_id=admin.admin_id, content_type=ContentTypeEnum.TEXT, status=PostStatusEnum.DRAFT)
    crud.create_post(db_session, channel_id=channel.channel_id, admin_id=admin.admin_id, content_type=ContentTypeEnum.TEXT, status=PostStatusEnum.SCHEDULED)
    crud.create_post(db_session, channel_id=channel.channel_id, admin_id=admin.admin_id, content_type=ContentTypeEnum.TEXT, status=PostStatusEnum.SCHEDULED)

    draft_posts = crud.get_posts_by_status(db_session, status=PostStatusEnum.DRAFT)
    assert len(draft_posts) == 1

    scheduled_posts = crud.get_posts_by_status(db_session, status=PostStatusEnum.SCHEDULED)
    assert len(scheduled_posts) == 2
    # Check ordering by publish_at (asc) if publish_at was varied
    # For now, publish_at is not set in these test posts, so order might not be guaranteed beyond insertion.
    # The crud.get_posts_by_status orders by publish_at.asc() by default.

def test_update_post_status(db_session: SQLAlchemySession):
    admin = crud.create_admin(db_session, admin_id=104)
    channel = crud.create_channel(db_session, channel_id=-10401, admin_id=admin.admin_id)

    post = crud.create_post(db_session, channel_id=channel.channel_id, admin_id=admin.admin_id, content_type=ContentTypeEnum.TEXT, status=PostStatusEnum.DRAFT)
    assert post.post_id is not None # Ensure post_id is available

    updated_post = crud.update_post_status(db_session, post_id=post.post_id, new_status=PostStatusEnum.PUBLISHED, error_message="Test Error")
    assert updated_post is not None
    assert updated_post.status == PostStatusEnum.PUBLISHED
    assert updated_post.error_message == "Test Error"

    retrieved_post = crud.get_post(db_session, post.post_id)
    assert retrieved_post is not None
    assert retrieved_post.status == PostStatusEnum.PUBLISHED
    assert retrieved_post.error_message == "Test Error"

    # Test updating a non-existent post
    non_existent_updated = crud.update_post_status(db_session, post_id=99999, new_status=PostStatusEnum.PUBLISHED)
    assert non_existent_updated is None
