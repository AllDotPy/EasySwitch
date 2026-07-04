import pytest
from unittest.mock import AsyncMock, MagicMock
import json
import hmac
import hashlib

from easyswitch.integrators.paystack import PaystackAdapter
from easyswitch.exceptions import UnsupportedOperationError
from easyswitch.types import TransactionDetail, Currency, TransactionStatus


@pytest.fixture
def adapter():
    class DummyPaystackAdapter(PaystackAdapter):
        def format_transaction(self, x): return x
        def get_normalize_status(self, status): return status

    return DummyPaystackAdapter(
        config=MagicMock(api_key="test_key", callback_url="https://callback.url"),
        context={}
    )


# small helper that acts as an async context manager returning the provided object
class _AsyncCtx:
    def __init__(self, obj):
        self._obj = obj

    async def __aenter__(self):
        return self._obj

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_validate_webhook_valid_signature(adapter):
    """Should return True for valid webhook signature."""
    payload = {"event": "charge.success", "data": {"id": 123}}
    sig = hmac.new(
        b"test_key",
        msg=json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"),
        digestmod=hashlib.sha512
    ).hexdigest()
    headers = {"x-paystack-signature": sig}

    result = adapter.validate_webhook(payload, headers)
    assert result is True


@pytest.mark.asyncio
async def test_validate_webhook_invalid_signature(adapter):
    """Should return False for invalid signature."""
    payload = {"event": "charge.success"}
    headers = {"x-paystack-signature": "invalid"}

    result = adapter.validate_webhook(payload, headers)
    assert result is False


@pytest.mark.asyncio
async def test_send_payment_success(adapter):
    """Should return PaymentResponse on successful init."""
    transaction = TransactionDetail(
        transaction_id="tx_1",
        amount=500.0,
        currency=Currency.NGN,
        customer=MagicMock(email="user@example.com", phone_number="+2348012345678"),
        provider=None,
        reference="order_123",
        callback_url="https://callback.url",
    )

    # Mock client and response
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.data = {
        "status": True,
        "data": {
            "reference": "ref123",
            "authorization_url": "https://paystack.com/pay/ref123",
            "access_code": "AC_123"
        }
    }
    mock_client.post.return_value = mock_response

    # make get_client() return an async context manager that yields mock_client
    adapter.get_client = lambda: _AsyncCtx(mock_client)

    response = await adapter.send_payment(transaction)

    assert response.reference == "ref123"
    assert response.payment_link == "https://paystack.com/pay/ref123"
    assert response.status == TransactionStatus.PENDING


@pytest.mark.asyncio
async def test_check_status_success(adapter):
    """Should return TransactionStatusResponse on success."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.data = {
        "status": True,
        "data": {"id": 1, "status": "success", "amount": 10000, "reference": "ref_123"}
    }
    mock_client.get.return_value = mock_response

    adapter.get_client = lambda: _AsyncCtx(mock_client)

    result = await adapter.check_status("ref_123")

    assert result.amount == 100.0  # since /100


@pytest.mark.asyncio
async def test_cancel_transaction_raises(adapter):
    """Paystack does not support cancel; should raise."""
    with pytest.raises(UnsupportedOperationError):
        await adapter.cancel_transaction("tx_1")
