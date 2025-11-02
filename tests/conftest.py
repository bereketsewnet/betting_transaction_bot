"""Pytest configuration and fixtures."""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.services.api_client import APIClient
from app.storage.memory_storage import MemoryStorage
from app.storage import StorageInterface


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_api_client():
    """Mock API client."""
    client = AsyncMock(spec=APIClient)
    return client


@pytest.fixture
def storage():
    """In-memory storage for tests."""
    return MemoryStorage()


@pytest.fixture
def mock_bot():
    """Mock Telegram bot."""
    bot = AsyncMock()
    bot.token = "test_token"
    return bot


@pytest.fixture
def sample_language():
    """Sample language data."""
    return {
        "code": "en",
        "name": "English",
        "isActive": True
    }


@pytest.fixture
def sample_deposit_bank():
    """Sample deposit bank data."""
    return {
        "id": 1,
        "bankName": "Test Bank",
        "accountNumber": "1234567890",
        "accountName": "Test Account",
        "notes": "Test notes",
        "isActive": True
    }


@pytest.fixture
def sample_transaction():
    """Sample transaction data."""
    return {
        "id": 1,
        "transactionUuid": "test-uuid-123",
        "type": "DEPOSIT",
        "amount": "100.00",
        "currency": "ETB",
        "status": "Pending",
        "depositBankId": 1,
        "bettingSiteId": 1,
        "playerSiteId": "player123",
        "createdAt": "2025-01-01T00:00:00Z"
    }

