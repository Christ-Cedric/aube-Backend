import pytest
import uuid
from app.models.subscription import SubscriptionRequest
from app.services.subscription_service import SubscriptionService
from app.utils.exceptions import ConflictError
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_create_subscription_request():
    # Mock DB
    mock_db = MagicMock()
    mock_collection = AsyncMock()
    mock_db.subscriptions = mock_collection
    
    service = SubscriptionService(mock_db)
    
    # Mock find_one to return None (no existing sub)
    mock_collection.find_one.return_value = None
    
    request = SubscriptionRequest(
        device_id=uuid.uuid4(),
        phone_number="+1234567890",
        months=1
    )
    
    result = await service.create_subscription_request(request)
    
    assert result.status == "pending"
    assert result.activation_key.startswith("ACT-")
    mock_collection.insert_one.assert_called_once()

@pytest.mark.asyncio
async def test_duplicate_subscription():
    mock_db = MagicMock()
    mock_collection = AsyncMock()
    mock_db.subscriptions = mock_collection
    
    service = SubscriptionService(mock_db)
    
    # Existing sub
    mock_collection.find_one.return_value = {"status": "pending"}
    
    request = SubscriptionRequest(
        device_id=uuid.uuid4(),
        phone_number="+1234567890",
        months=1
    )
    
    with pytest.raises(ConflictError):
        await service.create_subscription_request(request)
