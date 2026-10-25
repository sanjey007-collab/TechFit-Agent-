import pytest
import pytest_asyncio
import os
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from apps.api.main import app as api_app
from apps.api.database import Base, get_db
from apps.api.seed import seed_backend
from apps.api.services.store_client import set_test_store_app
from apps.mock_store.main import app as mock_store_app
from apps.mock_store.seed import seed_mock_store
from apps.mock_store.database import Base as MockStoreBase, get_db as get_mock_store_db

TEST_DB_URL = "sqlite+aiosqlite:///./test_techfit.db"
test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)

TEST_MOCK_STORE_DB_URL = "sqlite+aiosqlite:///./test_mock_store.db"
test_mock_store_engine = create_async_engine(TEST_MOCK_STORE_DB_URL, echo=False)
TestMockStoreSessionLocal = async_sessionmaker(test_mock_store_engine, expire_on_commit=False, class_=AsyncSession)

async def override_get_db():
    async with TestSessionLocal() as session:
        yield session

async def override_get_mock_store_db():
    async with TestMockStoreSessionLocal() as session:
        yield session

api_app.dependency_overrides[get_db] = override_get_db
mock_store_app.dependency_overrides[get_mock_store_db] = override_get_mock_store_db

@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_test_databases():
    # Set the in-memory test store app so API routers can query mock store directly
    set_test_store_app(mock_store_app)

    # 1. Reset and seed test backend DB
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await seed_backend(custom_engine=test_engine, custom_session_factory=TestSessionLocal)

    # 2. Reset and seed test mock store DB
    async with test_mock_store_engine.begin() as conn:
        await conn.run_sync(MockStoreBase.metadata.drop_all)
        await conn.run_sync(MockStoreBase.metadata.create_all)
    await seed_mock_store(custom_engine=test_mock_store_engine, custom_session_factory=TestMockStoreSessionLocal)

    yield

    # Cleanup
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    async with test_mock_store_engine.begin() as conn:
        await conn.run_sync(MockStoreBase.metadata.drop_all)
    if os.path.exists("./test_techfit.db"):
        try:
            os.remove("./test_techfit.db")
        except Exception:
            pass
    if os.path.exists("./test_mock_store.db"):
        try:
            os.remove("./test_mock_store.db")
        except Exception:
            pass

@pytest_asyncio.fixture
async def api_client():
    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

@pytest_asyncio.fixture
async def store_client():
    transport = ASGITransport(app=mock_store_app)
    async with AsyncClient(transport=transport, base_url="http://teststore") as client:
        yield client
