import base64
import hmac
import hashlib
import json
from datetime import datetime
from unittest.mock import AsyncMock, patch
import pytest

from easyswitch.integrators.klarna import KlarnaIntegrator
from easyswitch.types import (
    Currency,
    CustomerInfo,
    TransactionDetail,
    TransactionStatus,
)
from easyswitch.exceptions import PaymentError


# -------------------------
# Fixtures
# -------------------------

@pytest.fixture
def klarna_config():
    return {
        "api_username": "test_user",
        "api_key": "test_key",
        "environment": "sandbox",
        "webhook_secret": "secret123",
    }


@pytest.fixture
def klarna_integrator(klarna_config):
    return KlarnaIntegrator(klarna_config)


@pytest.fixture
def sample_transaction():
    return TransactionDetail(
        transaction_id="txn_123",
        reference="order_456",
        amount=100.0,
        currency=Currency.EUR,
        customer=CustomerInfo(
            email="user@example.com",
            first_name="Jane",
            last_name="Doe",
            country="SE",
        ),
        callback_url="https://example.com/callback",
    )


# -------------------------
# Unit Tests
# -------------------------

def test_validate_credentials(klarna_integrator):
    """Validate that credentials check works properly."""
    assert klarna_integrator.validate_credentials() is True

    # Missing username should fail
    klarna_integrator.config.api_username = None
    assert klarna_integrator.validate_credentials() is False


def test_get_credentials(klarna_integrator):
    """Test credential dictionary."""
    creds = klarna_integrator.get_credentials()
    assert creds["api_username"] == "test_user"
    assert creds["api_key"] == "test_key"


@pytest.mark.asyncio
async def test_get_headers(klarna_integrator):
    """Ensure headers include proper Base64 encoded auth."""
    headers = await klarna_integrator.get_headers()
    assert "Authorization" in headers
    decoded = base64.b64decode(headers["Authorization"].split()[1]).decode()
    assert decoded == "test_user:test_key"
    assert headers["Content-Type"] == "application/json"


def test_get_normalize_status(klarna_integrator):
    """Test mapping of Klarna payment statuses."""
    assert klarna_integrator.get_normalize_status("AUTHORIZED") == TransactionStatus.PENDING
    assert klarna_integrator.get_normalize_status("CAPTURED") == TransactionStatus.SUCCESSFUL
    assert klarna_integrator.get_normalize_status("REFUNDED") == TransactionStatus.REFUNDED
    assert klarna_integrator.get_normalize_status("FAILED") == TransactionStatus.FAILED
    assert klarna_integrator.get_normalize_status("XYZ") == TransactionStatus.UNKNOWN


def test_validate_webhook_valid(klarna_integrator):
    """Validate correct webhook signature."""
    payload = {"event": "payment.update", "amount": 100}
    raw_body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    signature = hmac.new(
        klarna_integrator.config.webhook_secret.encode(),
        raw_body,
        hashlib.sha256
    ).hexdigest()
    headers = {"klarna-signature": signature}
    assert klarna_integrator.validate_webhook(raw_body, headers) is True


def test_validate_webhook_invalid(klarna_integrator):
    """Fail validation for wrong signature."""
    payload = {"event": "payment.update"}
    raw_body = json.dumps(payload).encode()
    headers = {"klarna-signature": "invalid"}
    assert klarna_integrator.validate_webhook(raw_body, headers) is False


def test_parse_webhook_valid(klarna_integrator):
    """Parse valid Klarna webhook payload."""
    payload = {
        "event_type": "payment.update",
        "order_id": "ord_001",
        "status": "CAPTURED",
        "amount": 5000,
        "currency": "EUR",
    }
    raw_body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    sig = hmac.new(
        klarna_integrator.config.webhook_secret.encode(),
        raw_body,
        hashlib.sha256
    ).hexdigest()

    headers = {"klarna-signature": sig}
    event = klarna_integrator.parse_webhook(payload, headers)
    assert event.transaction_id == "ord_001"
    assert event.status == TransactionStatus.SUCCESSFUL
    assert event.amount == 5000
    assert event.provider == "klarna"


def test_parse_webhook_invalid_signature(klarna_integrator):
    """Ensure invalid signature raises PaymentError."""
    payload = {"order_id": "ord_002", "status": "FAILED"}
    headers = {"klarna-signature": "wrong"}
    with pytest.raises(PaymentError):
        klarna_integrator.parse_webhook(payload, headers)


def test_format_transaction_valid(klarna_integrator, sample_transaction):
    """Ensure valid transaction formatting for Klarna API."""
    formatted = klarna_integrator.format_transaction(sample_transaction)
    assert formatted["purchase_country"] == "SE"
    assert formatted["order_amount"] == 10000  # 100 * 100
    assert "merchant_urls" in formatted
    assert formatted["merchant_urls"]["confirmation"].startswith("https://")


def test_format_transaction_missing_email(klarna_integrator, sample_transaction):
    """Email is required for Klarna payments."""
    sample_transaction.customer.email = None
    with pytest.raises(PaymentError):
        klarna_integrator.format_transaction(sample_transaction)


@pytest.mark.asyncio
async def test_send_payment_success(klarna_integrator, sample_transaction):
    """Mock successful Klarna payment creation."""
    mock_response = AsyncMock()
    mock_response.status = 201
    mock_response.json.return_value = {
        "session_id": "sess_123",
        "redirect_url": "https://klarna.com/pay",
        "client_token": "token_123",
    }

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response

    with patch.object(klarna_integrator, "get_client", return_value=mock_client):
        result = await klarna_integrator.send_payment(sample_transaction)

    assert result.transaction_id == "sess_123"
    assert result.payment_link == "https://klarna.com/pay"
    assert result.transaction_token == "token_123"
    assert result.status == TransactionStatus.PENDING.value


@pytest.mark.asyncio
async def test_send_payment_failure(klarna_integrator, sample_transaction):
    """Handle Klarna payment API error."""
    mock_response = AsyncMock()
    mock_response.status = 400
    mock_response.json.return_value = {"error": "Invalid request"}

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response

    with patch.object(klarna_integrator, "get_client", return_value=mock_client):
        with pytest.raises(PaymentError):
            await klarna_integrator.send_payment(sample_transaction)


@pytest.mark.asyncio
async def test_check_status_success(klarna_integrator):
    """Mock successful Klarna status check."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"status": "CAPTURED", "order_amount": 5000, "purchase_currency": "EUR"}

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    with patch.object(klarna_integrator, "get_client", return_value=mock_client):
        result = await klarna_integrator.check_status("ord_001")

    assert result.status == TransactionStatus.SUCCESSFUL
    assert result.amount == 50.0  # 5000 / 100
    assert result.transaction_id == "ord_001"


@pytest.mark.asyncio
async def test_refund_success(klarna_integrator):
    """Mock successful Klarna refund."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"refunded_amount": 5000, "currency": "EUR"}

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response

    with patch.object(klarna_integrator, "get_client", return_value=mock_client):
        result = await klarna_integrator.refund("ord_001", amount=50.0)

    assert result.status == TransactionStatus.REFUNDED.value
    assert result.amount == 50.0
    assert result.transaction_id == "ord_001"


@pytest.mark.asyncio
async def test_cancel_transaction_success(klarna_integrator):
    """Mock successful Klarna transaction cancellation."""
    mock_response = AsyncMock()
    mock_response.status = 200

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response

    with patch.object(klarna_integrator, "get_client", return_value=mock_client):
        # Should not raise
        await klarna_integrator.cancel_transaction("ord_001")


@pytest.mark.asyncio
async def test_get_transaction_detail_success(klarna_integrator):
    """Mock retrieving Klarna transaction details."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "status": "CAPTURED",
        "order_amount": 5000,
        "purchase_currency": "EUR",
        "billing_address": {
            "email": "user@example.com",
            "phone": "+46700000000",
            "given_name": "Jane",
            "family_name": "Doe",
        },
        "order_id": "ord_001"
    }

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    with patch.object(klarna_integrator, "get_client", return_value=mock_client):
        result = await klarna_integrator.get_transaction_detail("ord_001")

    assert result.transaction_id == "ord_001"
    assert result.amount == 50.0
    assert result.currency == "EUR"
    assert result.customer.email == "user@example.com"
    assert result.status == TransactionStatus.SUCCESSFUL
