"""
EasySwitch - Airtel Money Integrator
"""

import hmac
import hashlib
import json
import base64
from typing import ClassVar, List, Dict, Optional, Any
from datetime import datetime

from easyswitch.adapters.base import AdaptersRegistry, BaseAdapter
from easyswitch.types import (Currency, PaymentResponse, WebhookEvent,
                              TransactionDetail, TransactionStatusResponse,
                              CustomerInfo, TransactionStatus)
from easyswitch.exceptions import PaymentError, UnsupportedOperationError


@AdaptersRegistry.register()
class AirtelMoneyAdapter(BaseAdapter):
    """Airtel Money Adapter for EasySwitch SDK."""
    
    SANDBOX_URL: str = "https://openapiuat.airtel.africa"
    PRODUCTION_URL: str = "https://openapi.airtel.africa"

    SUPPORTED_CURRENCIES: ClassVar[List[Currency]] = [
        Currency.UGX,  # Uganda
        Currency.TZS,  # Tanzania
        Currency.KES,  # Kenya
        Currency.RWF,  # Rwanda
        Currency.ZMW,  # Zambia
        Currency.MWK,  # Malawi
        Currency.NGN,  # Nigeria
        Currency.CDF,  # Democratic Republic of Congo
        Currency.XOF,  # West Africa (Senegal, Guinea Bissau, etc.)
        Currency.GHS,  # Ghana
        Currency.BIF,  # Burundi
        Currency.ETB,  # Ethiopia
        Currency.BWP,  # Botswana
        Currency.ZWL,  # Zimbabwe (or USD commonly used)
    ]

    MIN_AMOUNT: ClassVar[Dict[Currency, float]] = {
        Currency.UGX: 500.0,
        Currency.TZS: 500.0,
        Currency.KES: 10.0,
        Currency.RWF: 100.0,
        Currency.ZMW: 1.0,
        Currency.MWK: 100.0,
        Currency.NGN: 50.0,
        Currency.CDF: 500.0,
        Currency.XOF: 100.0,
        Currency.GHS: 1.0,
        Currency.BIF: 500.0,
        Currency.ETB: 10.0,
        Currency.BWP: 1.0,
        Currency.ZWL: 100.0,
    }

    MAX_AMOUNT: ClassVar[Dict[Currency, float]] = {
        Currency.UGX: 10_000_000,
        Currency.TZS: 10_000_000,
        Currency.KES: 500_000,
        Currency.RWF: 5_000_000,
        Currency.ZMW: 50_000,
        Currency.MWK: 5_000_000,
        Currency.NGN: 1_000_000,
        Currency.CDF: 10_000_000,
        Currency.XOF: 5_000_000,
        Currency.GHS: 50_000,
        Currency.BIF: 10_000_000,
        Currency.ETB: 500_000,
        Currency.BWP: 50_000,
        Currency.ZWL: 10_000_000,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

    def validate_credentials(self) -> bool:
        """Validate the credentials for Airtel Money."""
        return bool(
            self.config.api_key and 
            getattr(self.config, "client_id", None) and
            getattr(self.config, "client_secret", None)
        )

    def get_credentials(self):
        """Return API credentials."""
        return {
            "client_id": getattr(self.config, "client_id", None),
            "client_secret": getattr(self.config, "client_secret", None),
            "api_key": self.config.api_key,
        }

    async def _get_access_token(self) -> str:
        """Get or refresh OAuth access token."""
        if self._access_token and self._token_expiry:
            if datetime.now() < self._token_expiry:
                return self._access_token

        client_id = getattr(self.config, "client_id", None)
        client_secret = getattr(self.config, "client_secret", None)

        if not client_id or not client_secret:
            raise PaymentError("Missing client_id or client_secret")

        async with self.get_client() as client:
            response = await client.post(
                "/auth/oauth2/token",
                json={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "grant_type": "client_credentials"
                },
                headers={"Content-Type": "application/json"}
            )

            data = response.json() if hasattr(response, "json") else response.data
            if response.status in range(200, 300):
                self._access_token = data.get("access_token")
                expires_in = data.get("expires_in", 3600)
                from datetime import timedelta
                self._token_expiry = datetime.now() + timedelta(seconds=expires_in - 300)
                return self._access_token

            raise PaymentError(
                message="Failed to obtain access token",
                status_code=response.status,
                raw_response=data
            )

    async def get_headers(self, authorization=True, **kwargs) -> Dict[str, str]:
        """Return headers for Airtel Money requests."""
        headers = {
            "Content-Type": "application/json",
            "X-Country": kwargs.get("country", "NG"),
            "X-Currency": kwargs.get("currency", "NGN"),
        }
        
        if authorization:
            token = await self._get_access_token()
            headers["Authorization"] = f"Bearer {token}"
        
        return headers
    
    def get_normalize_status(self, status: str) -> TransactionStatus:
        """Normalize Airtel Money transaction status."""
        mapping = {
            "ts": TransactionStatus.SUCCESSFUL,  # Transaction Successful
            "tf": TransactionStatus.FAILED,      # Transaction Failed
            "ta": TransactionStatus.PENDING,     # Transaction Ambiguous
            "tp": TransactionStatus.PENDING,     # Transaction Pending
            "tn": TransactionStatus.FAILED,      # Transaction Not Found
            "tr": TransactionStatus.REFUNDED,    # Transaction Refunded
            "tc": TransactionStatus.CANCELLED,   # Transaction Cancelled
        }
        return mapping.get(status.lower(), TransactionStatus.UNKNOWN)

    def validate_webhook(self, raw_body: bytes, headers: Dict[str, str]) -> bool:
        """Validate the authenticity of an Airtel Money webhook."""
        signature = headers.get("x-airtel-signature") or headers.get("x-signature")
        secret_key = getattr(self.config, "webhook_secret", None) or self.config.api_key
        
        if not signature or not secret_key:
            return False

        computed_sig = hmac.new(
            secret_key.encode("utf-8"),
            msg=raw_body,
            digestmod=hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(computed_sig, signature)
    
    def parse_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> WebhookEvent:
        """Parse and validate an Airtel Money webhook."""
        raw_body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        
        if not self.validate_webhook(raw_body, headers):
            raise PaymentError("Invalid webhook signature", raw_response=payload)

        transaction = payload.get("transaction", {})
        event_type = payload.get("event_type", "payment_notification")
        transaction_id = transaction.get("id") or transaction.get("airtel_money_id")
        status_code = transaction.get("status", {}).get("code", "tn")
        status = self.get_normalize_status(status_code)
        amount = float(transaction.get("amount", 0))
        currency = transaction.get("currency", "NGN")
        
        metadata = {
            "message": transaction.get("status", {}).get("message"),
            "response_code": transaction.get("status", {}).get("response_code"),
        }
        
        context = {
            "msisdn": transaction.get("msisdn"),
            "country": headers.get("x-country"),
        }

        return WebhookEvent(
            event_type=event_type,
            provider=self.provider_name(),
            transaction_id=transaction_id,
            status=status,
            amount=amount,
            currency=currency,
            created_at=datetime.fromisoformat(transaction.get("created_at")) if transaction.get("created_at") else datetime.now(),
            raw_data=payload,
            metadata=metadata,
            context=context,
        )
    
    def format_transaction(self, transaction: TransactionDetail) -> Dict[str, Any]:
        """Convert standardized TransactionDetail into Airtel Money-specific payload."""
        self.validate_transaction(transaction)
        
        # Extract phone number from customer info
        msisdn = transaction.customer.phone_number
        if not msisdn:
            raise PaymentError("Phone number (msisdn) is required for Airtel Money")
        
        # Remove any non-digit characters
        msisdn = ''.join(filter(str.isdigit, msisdn))
        
        return {
            "reference": transaction.reference,
            "subscriber": {
                "country": getattr(transaction.customer, "country", "NG"),
                "currency": transaction.currency,
                "msisdn": msisdn
            },
            "transaction": {
                "amount": transaction.amount,
                "country": getattr(transaction.customer, "country", "NG"),
                "currency": transaction.currency,
                "id": transaction.transaction_id or transaction.reference
            }
        }
        
    async def send_payment(self, transaction: TransactionDetail) -> PaymentResponse:
        """Send a payment request to Airtel Money (Collection)."""
        payload = self.format_transaction(transaction)
        country = getattr(transaction.customer, "country", "NG")
        
        headers = await self.get_headers(
            country=country,
            currency=transaction.currency
        )

        async with self.get_client() as client:
            response = await client.post(
                "/merchant/v1/payments/",
                json=payload,
                headers=headers
            )

            data = response.json() if hasattr(response, "json") else response.data
            
            if response.status in range(200, 300):
                resp_data = data.get("data", {})
                transaction_data = resp_data.get("transaction", {})
                
                status_code = transaction_data.get("status", {}).get("code", "tp")
                
                return PaymentResponse(
                    transaction_id=transaction_data.get("id") or transaction_data.get("airtel_money_id"),
                    reference=transaction.reference,
                    provider=self.provider_name(),
                    status=self.get_normalize_status(status_code).value,
                    amount=transaction.amount,
                    currency=transaction.currency,
                    payment_link=None,  # Airtel Money uses USSD/App push
                    transaction_token=transaction_data.get("id"),
                    metadata={
                        "message": transaction_data.get("status", {}).get("message"),
                        "msisdn": payload["subscriber"]["msisdn"]
                    },
                    raw_response=data,
                )

            raise PaymentError(
                message=f"Payment request failed with status {response.status}",
                status_code=response.status,
                raw_response=data,
            )

    async def check_status(self, reference: str) -> TransactionStatusResponse:
        """Check the status of an Airtel Money transaction by reference."""
        # Airtel Money uses transaction ID for status check
        async with self.get_client() as client:
            headers = await self.get_headers()
            
            response = await client.get(
                f"/standard/v1/payments/{reference}",
                headers=headers
            )

            data = response.json() if hasattr(response, "json") else response.data
            
            if response.status in range(200, 300):
                resp_data = data.get("data", {})
                transaction = resp_data.get("transaction", {})
                
                status_code = transaction.get("status", {}).get("code", "tn")
                
                return TransactionStatusResponse(
                    transaction_id=transaction.get("id") or transaction.get("airtel_money_id"),
                    provider=self.provider_name(),
                    status=self.get_normalize_status(status_code),
                    amount=float(transaction.get("amount", 0)),
                    data=transaction,
                )

            raise PaymentError(
                message=f"Failed to verify transaction: {reference}",
                status_code=response.status,
                raw_response=data
            )

    async def cancel_transaction(self, transaction_id: str) -> None:
        """Airtel Money does not support transaction cancellation."""
        raise UnsupportedOperationError(self.provider_name())

    async def refund(self, transaction_id: str, amount: Optional[float] = None) -> PaymentResponse:
        """Refund an Airtel Money transaction."""
        async with self.get_client() as client:
            headers = await self.get_headers()
            
            payload = {
                "transaction": {
                    "airtel_money_id": transaction_id
                }
            }
            
            if amount:
                payload["transaction"]["amount"] = amount

            response = await client.post(
                "/standard/v1/payments/refund",
                json=payload,
                headers=headers
            )

            data = response.json() if hasattr(response, "json") else response.data
            
            if response.status in range(200, 300):
                refund_data = data.get("data", {})
                transaction = refund_data.get("transaction", {})
                
                status_code = transaction.get("status", {}).get("code", "tp")
                
                return PaymentResponse(
                    transaction_id=transaction_id,
                    reference=f"refund-{transaction_id}",
                    provider=self.provider_name(),
                    status=self.get_normalize_status(status_code).value,
                    amount=float(transaction.get("amount", amount or 0)),
                    currency=transaction.get("currency", "NGN"),
                    metadata={
                        "message": transaction.get("status", {}).get("message"),
                        "refund_id": transaction.get("id")
                    },
                    raw_response=data,
                )

            raise PaymentError(
                message=f"Refund failed with status {response.status}",
                status_code=response.status,
                raw_response=data,
            )
        
    async def get_transaction_detail(self, transaction_id: str) -> TransactionDetail:
        """Retrieve transaction details from Airtel Money by transaction ID."""
        async with self.get_client() as client:
            headers = await self.get_headers()
            
            response = await client.get(
                f"/standard/v1/payments/{transaction_id}",
                headers=headers
            )

            data = response.json() if hasattr(response, "json") else response.data
            
            if response.status in range(200, 300):
                resp_data = data.get("data", {})
                tx = resp_data.get("transaction", {})
                subscriber = resp_data.get("subscriber", {})

                customer = CustomerInfo(
                    email=None,  # Airtel Money typically doesn't provide email
                    phone_number=subscriber.get("msisdn"),
                    first_name=subscriber.get("first_name"),
                    last_name=subscriber.get("last_name"),
                    metadata={
                        "country": subscriber.get("country"),
                        "subscriber_type": subscriber.get("type")
                    },
                )

                status_code = tx.get("status", {}).get("code", "tn")
                
                return TransactionDetail(
                    transaction_id=tx.get("id") or tx.get("airtel_money_id", transaction_id),
                    provider=self.provider_name(),
                    amount=float(tx.get("amount", 0)),
                    currency=tx.get("currency", "NGN"),
                    status=self.get_normalize_status(status_code),
                    reference=tx.get("reference") or tx.get("id"),
                    callback_url=None,
                    created_at=datetime.fromisoformat(tx.get("created_at")) if tx.get("created_at") else datetime.now(),
                    updated_at=datetime.fromisoformat(tx.get("updated_at")) if tx.get("updated_at") else None,
                    completed_at=datetime.fromisoformat(tx.get("completed_at")) if tx.get("completed_at") else None,
                    customer=customer,
                    metadata={
                        "status_message": tx.get("status", {}).get("message"),
                        "response_code": tx.get("status", {}).get("response_code")
                    },
                    raw_data=resp_data
                )

            raise PaymentError(
                message=f"Failed to retrieve transaction {transaction_id}",
                status_code=response.status,
                raw_response=data
            )