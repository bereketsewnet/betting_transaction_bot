"""Tests for API client."""
import pytest
from unittest.mock import AsyncMock, patch
from pathlib import Path

from app.services.api_client import APIClient
from app.schemas.api_models import Language, DepositBank, TransactionResponse


@pytest.mark.asyncio
async def test_get_languages(mock_api_client):
    """Test getting languages."""
    mock_response = AsyncMock()
    mock_response.json.return_value = {
        "languages": [
            {"code": "en", "name": "English", "isActive": True}
        ]
    }
    mock_response.status_code = 200
    
    with patch.object(APIClient, "_request", return_value=mock_response):
        client = APIClient()
        languages = await client.get_languages()
        assert len(languages) == 1
        assert languages[0].code == "en"


@pytest.mark.asyncio
async def test_create_transaction_json(mock_api_client):
    """Test creating transaction with JSON."""
    mock_response = AsyncMock()
    mock_response.json.return_value = {
        "message": "Transaction created successfully",
        "transaction": {
            "id": 1,
            "transactionUuid": "test-uuid",
            "type": "DEPOSIT",
            "amount": "100.00",
            "currency": "ETB",
            "status": "Pending",
        }
    }
    mock_response.status_code = 201
    
    with patch.object(APIClient, "_request", return_value=mock_response):
        client = APIClient()
        transaction = await client.create_transaction(
            player_uuid="test-uuid",
            transaction_type="DEPOSIT",
            amount=100.0,
            currency="ETB",
            betting_site_id=1,
            player_site_id="player123",
            deposit_bank_id=1,
        )
        assert transaction.transaction.transactionUuid == "test-uuid"
        assert transaction.transaction.type == "DEPOSIT"


@pytest.mark.asyncio
async def test_get_deposit_banks(mock_api_client):
    """Test getting deposit banks."""
    mock_response = AsyncMock()
    mock_response.json.return_value = {
        "depositBanks": [
            {
                "id": 1,
                "bankName": "Test Bank",
                "accountNumber": "1234567890",
                "accountName": "Test Account",
                "isActive": True
            }
        ]
    }
    mock_response.status_code = 200
    
    with patch.object(APIClient, "_request", return_value=mock_response):
        client = APIClient()
        banks = await client.get_deposit_banks()
        assert len(banks) == 1
        assert banks[0].id == 1
        assert banks[0].bankName == "Test Bank"

