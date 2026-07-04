import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml

from easyswitch.client import EasySwitch
from easyswitch.exceptions import (ConfigurationError, InvalidProviderError,
                                   PaymentError)
from easyswitch.types import (Currency, CustomerInfo, PaymentResponse,
                              Provider, TransactionDetail, TransactionStatus)


# Fixtures
@pytest.fixture
def sample_config_dict():
    return {
        "providers": {
            "CINETPAY": {
                "api_key": "test_api_key",
                "extra": {
                    "site_id": "test_site_id",
                    "secret": "test_secret"
                }
            }
        },
        "default_provider": "CINETPAY"
    }

@pytest.fixture
def sample_transaction():
    return TransactionDetail(
        transaction_id="test123",
        provider=Provider.CINETPAY,
        amount=1000,
        currency=Currency.XOF,
        reference="order_123",
        customer=CustomerInfo(
            first_name="John",
            last_name="Doe",
            phone_number="+221771234567"
        ),
    )

@pytest.fixture
def mock_cinetpay_adapter():
    with patch('easyswitch.adapters.AdaptersRegistry.get') as mock:
        adapter = MagicMock()
        adapter.return_value.send_payment = AsyncMock(
            return_value=PaymentResponse(
                transaction_id="test123",
                provider=Provider.CINETPAY,
                status=TransactionStatus.PENDING,
                amount=1000,
                currency=Currency.XOF,
            )
        )
        adapter.return_value.check_status = AsyncMock(
            return_value=TransactionStatus.PENDING
        )
        mock.return_value = adapter
        yield

# Initialisation tests
def test_client_from_dict(sample_config_dict):
    """Test initialization from dictionary"""
    client = EasySwitch.from_dict(sample_config_dict)
    assert client.config.environment == "sandbox"
    assert Provider.CINETPAY in client.config.providers

def test_client_from_json(tmp_path, sample_config_dict):
    """Test initialization from JSON file"""
    json_file = tmp_path / "config.json"
    json_file.write_text(json.dumps(sample_config_dict))

    client = EasySwitch.from_json(json_file)
    assert client.config.default_provider == Provider.CINETPAY

def test_client_from_yaml(tmp_path, sample_config_dict):
    """Test initialization from YAML file"""
    yaml_file = tmp_path / "config.yaml"
    yaml_file.write_text(yaml.dump(sample_config_dict))

    client = EasySwitch.from_yaml(yaml_file)
    assert client.config.timeout == 30

def test_client_from_env(tmp_path):
    """Test initialization from environment variables"""
    env_file = tmp_path / ".env"
    env_content = "\n".join([
        "EASYSWITCH_ENVIRONMENT=sandbox",
        "EASYSWITCH_ENABLED_PROVIDERS=cinetpay",
        "EASYSWITCH_CINETPAY_API_KEY=test_api_key",
        "EASYSWITCH_CINETPAY_X_SITE_ID=test_site_id",
        "EASYSWITCH_CINETPAY_X_SECRET=test_secret"
    ])
    env_file.write_text(env_content)

    client = EasySwitch.from_env(env_file)
    assert Provider.CINETPAY in client.config.providers

def test_client_from_multi_sources(tmp_path):
    """Test initialization from multiple sources"""
    json_file = tmp_path / "base_config.json"
    json_file.write_text(json.dumps({
        "timeout": 30,
        "environment": "sandbox",
        "providers": {
            "CINETPAY": {
                "api_key": "test_api_key",
                "extra": {"site_id": "x", "secret": "x"}
            }
        }
    }))

    # Override environment via env file
    env_file = tmp_path / ".env"
    env_file.write_text("EASYSWITCH_ENVIRONMENT=production")

    client = EasySwitch.from_multi_sources(
        json_file=json_file,
        env_file=env_file
    )
    assert client.config.timeout == 30
    assert Provider.CINETPAY in client.config.providers

# Feature tests
def test_send_payment(sample_config_dict, sample_transaction, mock_cinetpay_adapter):
    """Test payment sending"""
    client = EasySwitch.from_dict(sample_config_dict)
    response = client.send_payment(
        transaction=sample_transaction,
        provider=Provider.CINETPAY,
    )

    assert response.status == TransactionStatus.PENDING
    assert response.transaction_id == "test123"

def test_send_payment_default_provider(sample_config_dict, sample_transaction, mock_cinetpay_adapter):
    """Test payment with default provider"""
    client = EasySwitch.from_dict(sample_config_dict)
    response = client.send_payment(transaction=sample_transaction)

    assert response.status == TransactionStatus.PENDING

def test_check_status(sample_config_dict, mock_cinetpay_adapter):
    """Test transaction status check"""
    client = EasySwitch.from_dict(sample_config_dict)
    status = client.check_status(
        provider=Provider.CINETPAY,
        transaction_id="test123"
    )

    assert status == TransactionStatus.PENDING

def test_invalid_provider(sample_config_dict, sample_transaction):
    """Test with invalid provider"""
    client = EasySwitch.from_dict(sample_config_dict)
    # Provider not in config
    with pytest.raises(InvalidProviderError):
        client.send_payment(
            transaction=sample_transaction,
            provider=Provider.PAYSTACK,
        )

def test_missing_provider_config():
    """Test with missing provider configuration"""
    with pytest.raises(ConfigurationError):
        EasySwitch.from_dict({
            "providers": {}  # No providers configured
        })

def test_payment_error(sample_config_dict, sample_transaction, mock_cinetpay_adapter):
    """Test payment error handling"""
    client = EasySwitch.from_dict(sample_config_dict)

    # Configure mock to raise error
    client._integrators[Provider.CINETPAY].send_payment = AsyncMock(
        side_effect=PaymentError("API error")
    )

    with pytest.raises(PaymentError):
        client.send_payment(
            transaction=sample_transaction,
            provider=Provider.CINETPAY,
        )

# Validation tests
def test_validate_providers(sample_config_dict):
    """Test provider validation"""
    client = EasySwitch.from_dict(sample_config_dict)
    assert Provider.CINETPAY in client._integrators

def test_missing_default_provider():
    """Test when default provider is missing"""
    config = {
        "providers": {
            "CINETPAY": {"api_key": "test", "extra": {"site_id": "x", "secret": "x"}}
        }
    }
    client = EasySwitch.from_dict(config)
    assert client.config.default_provider == Provider.CINETPAY  # Should be auto-set

# Integration tests (with mocks)
def test_full_payment_flow(sample_config_dict, sample_transaction, mock_cinetpay_adapter):
    """Test complete payment flow"""
    client = EasySwitch.from_dict(sample_config_dict)

    # Send payment
    payment_response = client.send_payment(
        transaction=sample_transaction,
        provider=Provider.CINETPAY,
    )

    # Check status
    status = client.check_status(
        provider=Provider.CINETPAY,
        transaction_id=payment_response.transaction_id
    )

    assert payment_response.status == TransactionStatus.PENDING
    assert status == TransactionStatus.PENDING
