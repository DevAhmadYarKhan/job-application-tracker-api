import pytest
from datetime import datetime, UTC
from typing import Annotated
from fastapi import Depends
from httpx import ASGITransport, AsyncClient
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_session
from app.models import User, Application
from app.services.auth import get_current_user


# We use an in-memory SQLite database for testing
# to avoid making changes to our main database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


engine = create_async_engine(TEST_DATABASE_URL, poolclass=StaticPool)


TestingSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, autoflush=False)


# Makes routes use the test database instead of the real database
async def override_get_session():
    async with TestingSessionLocal() as session:
        yield session


# Makes User 1 the logged-in user for every authenticated route
async def override_get_current_user(session: Annotated[AsyncSession, Depends(get_session)]):
    user = await session.get(User, 1)

    if user is None:
        raise RuntimeError("Test user 1 was not created")

    return user


app.dependency_overrides[get_session] = override_get_session
app.dependency_overrides[get_current_user] = override_get_current_user


# Ensure AnyIO runs tests using asyncio
@pytest.fixture
def anyio_backend():
    return "asyncio"


# Creates fresh database tables for every test
@pytest.fixture(autouse=True)
async def prepare_database():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


# Creates our test users. We get two users, user 1 and user 2
@pytest.fixture(autouse=True)
async def seed_database_users(prepare_database):
    async with TestingSessionLocal() as session:

        user_1 = User(
            id=1,
            email="user1@example.com",
            username="user1",
            password_hash="test_password",
        )

        user_2 = User(
            id=2,
            email="user2@example.com",
            username="user2",
            password_hash="test_password",
        )

        session.add_all([user_1, user_2])

        await session.commit()


# Creates applications for our test users. User 1 gets eight applications and user 2 gets one
@pytest.fixture
async def seed_database_applications(seed_database_users):
    async with TestingSessionLocal() as session:
        applications = [
            Application(
                company="Google",
                role="Backend Engineer",
                status="saved",
                user_id=1,
            ),
            Application(
                company="Microsoft",
                role="Software Engineer",
                status="applied",
                applied_at=datetime.now(UTC),
                user_id=1,
            ),
            Application(
                company="Amazon",
                role="Python Developer",
                status="interview",
                applied_at=datetime.now(UTC),
                user_id=1,
            ),
            Application(
                company="Meta",
                role="API Engineer",
                status="rejected",
                applied_at=datetime.now(UTC),
                user_id=1,
            ),
            Application(
                company="Spotify",
                role="Backend Developer",
                status="offer",
                applied_at=datetime.now(UTC),
                user_id=1,
            ),
            Application(
                company="Apple",
                role="Software Engineer",
                status="applied",
                applied_at=datetime.now(UTC),
                user_id=1,
            ),
            Application(
                company="Stripe",
                role="Backend Engineer",
                status="interview",
                applied_at=datetime.now(UTC),
                user_id=1,
            ),
            Application(
                company="GitHub",
                role="Platform Engineer",
                status="saved",
                user_id=1,
            ),
            Application(
                company="Netflix",
                role="Platform Engineer",
                status="saved",
                user_id=2,
            ),
        ]

        session.add_all(applications)
        await session.commit()


# Provides an async test client to each test
@pytest.fixture
async def client():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client



# Tests the GET /applications/ when applications do exist
@pytest.mark.anyio
async def test_get_applications(client, seed_database_applications):
    response = await client.get("/applications/")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 8

    companies = {application["company"] for application in data}

    assert companies == {
        "Google",
        "Microsoft",
        "Amazon",
        "Meta",
        "Spotify",
        "Apple",
        "Stripe",
        "GitHub"
    }


# Test  GET /applications/ endpoint when user has no applications
@pytest.mark.anyio
async def test_get_applications_when_none(client):
    response = await client.get("/applications/")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 0


 # Both tests below test GET /applications/ endpoint with query params
@pytest.mark.anyio
async def test_get_applications_query_params(client, seed_database_applications):
    response = await client.get("/applications/?status=saved&sort_by=created_at&order=desc&page=2&page_size=1")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    assert data[0]["company"] == "Google"


@pytest.mark.anyio
async def test_get_applications_query_params_2(client, seed_database_applications):
    response = await client.get("/applications/?status=interview&sort_by=applied_at&order=desc&page=1&page_size=5")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    companies = [application["company"] for application in data]

    assert companies == ["Stripe", "Amazon"]


# Test GET /applications/{id} endpoint when the application we want exists
@pytest.mark.anyio
async def test_get_application(client, seed_database_applications):
    response = await client.get("/applications/3")

    assert response.status_code == 200

    data = response.json()

    assert data["company"] == "Amazon"


# Test GET /applications/{id} endpoint when the application we want belongs to another user
@pytest.mark.anyio
async def test_get_application_when_foreign(client, seed_database_applications):
    response = await client.get("/applications/9")

    assert response.status_code == 404

    data = response.json()

    assert {"detail": "Application not found"}


# Test GET /applications/{id} endpoint when the application we want does not exist
@pytest.mark.anyio
async def test_get_application_when_none(client, seed_database_applications):
    response = await client.get("/applications/20")

    assert response.status_code == 404

    data = response.json()

    assert data == {"detail": "Application not found"}


# Test GET /applications/{id} endpoint when id is negative
@pytest.mark.anyio
async def test_get_application_when_negative(client, seed_database_applications):
    response = await client.get("/applications/-1")

    assert response.status_code == 422


# Test GET /applications/{id} endpoint when id cannot be parsed to int
@pytest.mark.anyio
async def test_get_application_when_unparsable(client, seed_database_applications):
    response = await client.get("/applications/one")

    assert response.status_code == 422