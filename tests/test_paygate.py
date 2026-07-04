import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from easyswitch.exceptions import PaymentError, UnsupportedOperationError, AuthenticationError
from easyswitch.integrators.paygate import PayGateAdapter
from easyswitch.types import Currency, CustomerInfo, TransactionDetail, TransactionStatus
from easyswitch.conf import ProviderConfig

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

def test_class_validate_credentials(paygate_adapter):
    """Test the class-level credentials validation"""
    from easyswitch.conf import ProviderConfig
    
    # Test valid credentials
    valid_creds = ProviderConfig(api_key="valid_key")
    assert PayGateAdapter.validate_credentials(valid_creds) is True
    
    # Test invalid credentials
    invalid_creds = ProviderConfig(api_key="")
    assert PayGateAdapter.validate_credentials(invalid_creds) is False

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
    """Test successful direct payment request"""
    mock_response = TransactionDetail(
            transaction_id="123",
            provider="PAYGATE",
            amount=100,
            currency=Currency.XOF,
            reference="REFERENCE1",
            customer=CustomerInfo(),
            status="0",
            created_at="2025-0513",
            transaction_type="PAYMENT",
            raw_data={}
        )
    
    with patch.object(paygate_adapter.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.data = mock_response
        
        response = await paygate_adapter.send_payment(sample_transaction)
        
        assert response.status == TransactionStatus.SUCCESSFUL
        assert response.reference == "paygate_ref_123"
        mock_post.assert_called_once()

@pytest.mark.asyncio
async def test_create_payment_link(paygate_adapter, sample_transaction):
    """Test payment link generation"""
    response = await paygate_adapter.create_payment_link(sample_transaction)
    
    assert response.payment_link is not None
    assert "token=test_api_key" in response.payment_link
    assert "amount=1000" in response.payment_link
    assert "identifier=test123" in response.payment_link

@pytest.mark.asyncio
async def test_check_status_success(paygate_adapter):
    """Test successful status check using v2 API"""
    mock_response = {
        "status": "0",  # 0 = success
        "amount": "1000",
        "payment_method": "FLOOZ",
        "datetime": "2023-01-01T12:00:00Z"
    }
    
    with patch.object(paygate_adapter.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.data = mock_response
        
        response = await paygate_adapter.check_status("test123")
        assert response.status == TransactionStatus.SUCCESSFUL
        assert response.amount == 1000
        assert "FLOOZ" in str(response.data)

def test_format_transaction(paygate_adapter, sample_transaction):
    """Test transaction formatting"""
    formatted = paygate_adapter.format_transaction(sample_transaction)
    
    assert formatted["amount"] == 1000  # XOF should be integer
    assert formatted["phone_number"] == "22890123456"
    assert formatted["identifier"] == "test123"
    assert formatted["network"] == "FLOOZ"  # Default value

def test_validate_credentials(paygate_adapter):
    """Test credentials validation"""
    assert paygate_adapter._validate_credentials() is True
    
    # Test with missing API key
    invalid_config = paygate_adapter.config.copy()
    invalid_config["api_key"] = ""
    adapter = PayGateAdapter(invalid_config)
    assert adapter._validate_credentials() is False

def test_get_normalize_status(paygate_adapter):
    """Test status normalization"""
    assert paygate_adapter.get_normalize_status("0") == TransactionStatus.SUCCESSFUL
    assert paygate_adapter.get_normalize_status("2") == TransactionStatus.ERROR  # Invalid auth
    assert paygate_adapter.get_normalize_status("4") == TransactionStatus.ERROR  # Invalid params
    assert paygate_adapter.get_normalize_status("6") == TransactionStatus.ERROR  # Duplicate
    assert paygate_adapter.get_normalize_status("99") == TransactionStatus.UNKNOWN

@pytest.mark.asyncio
async def test_get_balance_success(paygate_adapter):
    """Test successful balance check"""
    mock_response = {
        "flooz": "15000.50",
        "tmoney": "7500.25"
    }
    
    with patch.object(paygate_adapter.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.data = mock_response
        
        balances = await paygate_adapter.get_balance()
        assert balances["flooz"] == 15000.5
        assert balances["tmoney"] == 7500.25

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
    
    # Should not raise with valid payload
    assert paygate_adapter.validate_webhook(valid_payload, {}) is True
    
    # Test with missing required field
    invalid_payload = valid_payload.copy()
    del invalid_payload["tx_reference"]
    with pytest.raises(AuthenticationError):
        paygate_adapter.validate_webhook(invalid_payload, {})

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
    
    event = paygate_adapter.parse_webhook(payload, {})
    
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
    invalid_transaction = sample_transaction.copy()
    invalid_transaction.amount = 50  # Below minimum for XOF
    with pytest.raises(ValueError):
        paygate_adapter.validate_transaction(invalid_transaction)
        
    # Test with invalid currency
    invalid_transaction = sample_transaction.copy()
    invalid_transaction.currency = "USD"  # Not supported
    with pytest.raises(ValueError):
        paygate_adapter.validate_transaction(invalid_transaction)

def test_get_headers(paygate_adapter):
    """Test headers generation"""
    headers = paygate_adapter.get_headers()
    assert headers["Content-Type"] == "application/json"
    assert headers["Accept"] == "application/json"