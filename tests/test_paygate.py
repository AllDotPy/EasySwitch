import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import replace

from easyswitch.exceptions import (PaymentError, UnsupportedOperationError,
                                   ValidationError)
from easyswitch.integrators.paygate import PayGateAdapter
from easyswitch.types import (Currency, CustomerInfo, Provider,
                              TransactionDetail, TransactionStatus)
from easyswitch.conf import ProviderConfig


# Helper: async context manager that yields a provided object
class _AsyncCtx:
    def __init__(self, obj):
        self._obj = obj

    async def __aenter__(self):
        return self._obj

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.fixture
def paygate_config():
    return ProviderConfig(
        api_key="test_api_key",
        environment="sandbox",
        callback_url="https://example.com/callback"
    )

@pytest.fixture
def paygate_adapter(paygate_config):
    return PayGateAdapter(paygate_config)

def test_get_credentials(paygate_adapter):
    creds = paygate_adapter.get_credentials()
    assert creds["api_key"] == "test_api_key"

def test_validate_credentials(paygate_adapter):
    """Test credentials validation"""
    assert paygate_adapter.validate_credentials() is True

def test_map_fields(paygate_adapter):
    paygate_response = {
        "identifier": "trans123",
        "tx_reference": "ref456",
        "amount": 1000,
        "currency": "XOF",
        "status": "0",
        "network": "FLOOZ"
    }

    mapped = paygate_adapter.map_fields(paygate_response)
    assert mapped["transaction_id"] == "trans123"
    assert mapped["reference"] == "ref456"
    assert mapped["amount"] == 1000
    assert mapped["payment_method"] == "FLOOZ"

@pytest.mark.asyncio
async def test_get_transaction_detail(paygate_adapter):
    with patch.object(paygate_adapter, 'check_status', new_callable=AsyncMock) as mock_check:
        mock_check.return_value = MagicMock(
            amount=1000,
            status=TransactionStatus.SUCCESSFUL,
            data={"tx_reference": "ref123"}
        )

        details = await paygate_adapter.get_transaction_detail("test123")
        assert details.amount == 1000
        assert details.status == TransactionStatus.SUCCESSFUL

@pytest.fixture
def sample_transaction():
    return TransactionDetail(
        amount=1000,
        currency=Currency.XOF,
        transaction_id="test123",
        reference="order_123",
        provider=Provider.PAYGATE,
        customer=CustomerInfo(
            id="cust_123",
            first_name="John",
            last_name="Doe",
            phone_number="+22890123456",
            email="john.doe@example.com"
        ),
        reason="Test payment"
    )

@pytest.mark.asyncio
async def test_send_payment_success(paygate_adapter, sample_transaction):
    """Test successful payment link generation (send_payment builds a URL)"""
    response = await paygate_adapter.send_payment(sample_transaction)

    assert response.status == TransactionStatus.PENDING
    assert response.payment_link is not None
    assert "token=test_api_key" in response.payment_link

@pytest.mark.asyncio
async def test_check_status_success(paygate_adapter):
    """Test successful status check using v2 API"""
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.data = {
        "status": "0",
        "amount": 1000,
        "payment_method": "FLOOZ",
        "datetime": "2023-01-01T12:00:00Z"
    }

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response

    original_get_client = paygate_adapter.get_client
    paygate_adapter.get_client = lambda: _AsyncCtx(mock_client)

    try:
        response = await paygate_adapter.check_status("test123")
        assert response.status == TransactionStatus.SUCCESSFUL
        assert response.amount == 1000
    finally:
        paygate_adapter.get_client = original_get_client

def test_format_transaction(paygate_adapter, sample_transaction):
    """Test transaction formatting"""
    formatted = paygate_adapter.format_transaction(sample_transaction)

    assert formatted["amount"] == 1000  # XOF should be integer
    assert formatted["phone_number"] == "+22890123456"
    assert formatted["identifier"] == "test123"

def test_get_normalize_status(paygate_adapter):
    """Test status normalization"""
    assert paygate_adapter.get_normalize_status("0") == TransactionStatus.SUCCESSFUL
    assert paygate_adapter.get_normalize_status("2") == TransactionStatus.PENDING
    assert paygate_adapter.get_normalize_status("4") == TransactionStatus.EXPIRED
    assert paygate_adapter.get_normalize_status("6") == TransactionStatus.CANCELLED
    assert paygate_adapter.get_normalize_status("99") == TransactionStatus.UNKNOWN

@pytest.mark.asyncio
async def test_get_balance_success(paygate_adapter):
    """Test successful balance check"""
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.data = {
        "flooz": "15000.50",
        "tmoney": "7500.25"
    }

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response

    original_get_client = paygate_adapter.get_client
    paygate_adapter.get_client = lambda: _AsyncCtx(mock_client)

    try:
        balances = await paygate_adapter.get_balance()
        assert balances["flooz"] == 15000.5
        assert balances["tmoney"] == 7500.25
    finally:
        paygate_adapter.get_client = original_get_client

def test_webhook_validation(paygate_adapter):
    """Test webhook payload validation"""
    valid_payload = {
        "tx_reference": "paygate_ref_123",
        "identifier": "test123",
        "amount": "1000",
        "status": "0",
        "payment_method": "FLOOZ",
        "datetime": "2023-01-01T12:00:00Z"
    }

    assert paygate_adapter.validate_webhook(valid_payload, {"x-test": "1"}) is True

    # Test with missing required field
    invalid_payload = valid_payload.copy()
    del invalid_payload["tx_reference"]
    assert paygate_adapter.validate_webhook(invalid_payload, {"x-test": "1"}) is False

def test_parse_webhook(paygate_adapter):
    """Test webhook parsing"""
    payload = {
        "tx_reference": "paygate_ref_123",
        "identifier": "test123",
        "amount": "1000",
        "status": "0",
        "payment_method": "FLOOZ",
        "datetime": "2023-01-01T12:00:00Z"
    }

    event = paygate_adapter.parse_webhook(payload, {"x-test": "1"})

    assert event.transaction_id == "test123"
    assert event.amount == 1000
    assert event.event_type == "payment_0"
    assert event.provider == "PAYGATE"

@pytest.mark.asyncio
async def test_cancel_transaction_not_supported(paygate_adapter):
    """Test that cancel operation raises proper exception"""
    with pytest.raises(UnsupportedOperationError):
        await paygate_adapter.cancel_transaction("test123")

@pytest.mark.asyncio
async def test_refund_not_supported(paygate_adapter):
    """Test that refund operation raises proper exception"""
    with pytest.raises(UnsupportedOperationError):
        await paygate_adapter.refund("test123")

def test_validate_transaction(paygate_adapter, sample_transaction):
    """Test transaction validation"""
    assert paygate_adapter.validate_transaction(sample_transaction) is True

    # Test with invalid amount
    invalid_transaction = replace(sample_transaction, amount=50)
    with pytest.raises(ValidationError):
        paygate_adapter.validate_transaction(invalid_transaction)

    # Test with invalid currency
    invalid_transaction = replace(sample_transaction, currency=Currency.USD)
    with pytest.raises(ValidationError):
        paygate_adapter.validate_transaction(invalid_transaction)

def test_get_headers(paygate_adapter):
    """Test headers generation"""
    headers = paygate_adapter.get_headers()
    assert headers["Content-Type"] == "application/json"
    assert headers["Accept"] == "application/json"
