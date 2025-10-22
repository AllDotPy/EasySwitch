"""
EasySwitch - Klarna Adapter
"""

import hmac
import hashlib
import json
import base64
from typing import ClassVar, List, Dict, Optional, Any
from datetime import datetime

from easyswitch.adapters.base import IntegratorRegistry, BaseIntegrator
from easyswitch.types import (
    Currency,
    PaymentResponse,
    WebhookEvent,
    TransactionDetail,
    TransactionStatusResponse,
    CustomerInfo,
    TransactionStatus,
)
from easyswitch.exceptions import PaymentError


@IntegratorRegistry.register()
class KlarnaAdapter(BaseIntegrator):
    """Klarna Payment Adapter for EasySwitch SDK."""

    SANDBOX_URL: str = "https://api.playground.klarna.com"
    PRODUCTION_URL: str = "https://api.klarna.com"

    SUPPORTED_CURRENCIES: ClassVar[List[Currency]] = [
        Currency.EUR,
        Currency.USD,
        Currency.GBP,
        Currency.SEK,
        Currency.NOK,
        Currency.DKK,
    ]

    MIN_AMOUNT: ClassVar[Dict[Currency, float]] = {
        Currency.EUR: 1.0,
        Currency.USD: 1.0,
        Currency.GBP: 1.0,
        Currency.SEK: 10.0,
        Currency.NOK: 10.0,
        Currency.DKK: 10.0,
    }

    MAX_AMOUNT: ClassVar[Dict[Currency, float]] = {
        Currency.EUR: 100000.0,
        Currency.USD: 100000.0,
        Currency.GBP: 100000.0,
        Currency.SEK: 1000000.0,
        Currency.NOK: 1000000.0,
        Currency.DKK: 1000000.0,
    }

    def validate_credentials(self) -> bool:
        """Validate Klarna API credentials from extra config."""
        extra = getattr(self.config, "extra", {}) or {}
        return bool(extra.get("api_username") and extra.get("api_key"))

    def get_credentials(self) -> Dict[str, str]:
        """Return Klarna API credentials from extra config."""
        extra = getattr(self.config, "extra", {}) or {}
        return {
            "api_username": extra.get("api_username"),
            "api_key": extra.get("api_key"),
        }

    async def get_headers(self, **kwargs) -> Dict[str, str]:
        """Return authorization headers for Klarna."""
        creds = self.get_credentials()
        credentials = f"{creds['api_username']}:{creds['api_key']}"
        encoded = base64.b64encode(credentials.encode()).decode()

        return {
            "Content-Type": "application/json",
            "Authorization": f"Basic {encoded}",
        }

    def get_normalize_status(self, status: str) -> TransactionStatus:
        """Normalize Klarna transaction statuses."""
        mapping = {
            "AUTHORIZED": TransactionStatus.PENDING,
            "CAPTURED": TransactionStatus.SUCCESSFUL,
            "CANCELLED": TransactionStatus.CANCELLED,
            "REFUNDED": TransactionStatus.REFUNDED,
            "FAILED": TransactionStatus.FAILED,
        }
        return mapping.get(status.upper(), TransactionStatus.UNKNOWN)

    def validate_webhook(self, raw_body: bytes, headers: Dict[str, str]) -> bool:
        """Validate Klarna webhook signature if webhook_secret is configured."""
        signature = headers.get("klarna-signature")
        secret = getattr(self.config, "extra", {}).get("webhook_secret")
        if not signature or not secret:
            return True  # Optional verification

        computed_sig = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, computed_sig)

    def parse_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> WebhookEvent:
        """Parse Klarna webhook events."""
        raw_body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")

        if not self.validate_webhook(raw_body, headers):
            raise PaymentError("Invalid Klarna webhook signature")

        order_id = payload.get("order_id")
        status = self.get_normalize_status(payload.get("status", "UNKNOWN"))

        return WebhookEvent(
            event_type=payload.get("event_type", "payment.update"),
            provider=self.provider_name(),
            transaction_id=order_id,
            status=status,
            amount=float(payload.get("amount", 0)),
            currency=payload.get("currency", "EUR"),
            created_at=datetime.utcnow(),
            raw_data=payload,
        )

    def format_transaction(self, transaction: TransactionDetail) -> Dict[str, Any]:
        """Convert standardized TransactionDetail into Klarna API payload."""
        self.validate_transaction(transaction)
        customer = transaction.customer

        if not customer or not customer.email:
            raise PaymentError("Customer email is required for Klarna payment")

        callback_url = (
            transaction.callback_url
            or getattr(self.config, "callback_url", None)
            or getattr(self.config.extra, "callback_url", "https://example.com/callback")
        )

        return {
            "purchase_country": getattr(customer, "country", "SE"),
            "purchase_currency": transaction.currency,
            "locale": "en-SE",
            "order_amount": int(transaction.amount * 100),
            "order_tax_amount": 0,
            "order_lines": [
                {
                    "name": "EasySwitch Payment",
                    "quantity": 1,
                    "unit_price": int(transaction.amount * 100),
                    "total_amount": int(transaction.amount * 100),
                }
            ],
            "merchant_urls": {
                "confirmation": callback_url,
                "notification": callback_url,
            },
        }

    async def send_payment(self, transaction: TransactionDetail) -> PaymentResponse:
        """Initiate a Klarna payment session."""
        payload = self.format_transaction(transaction)
        headers = await self.get_headers()

        async with self.get_client() as client:
            response = await client.post("/payments/v1/sessions", json_data=payload, headers=headers)
            data = getattr(response, "json", lambda: response.data)()

            if response.status in range(200, 300):
                return PaymentResponse(
                    transaction_id=data.get("session_id"),
                    reference=transaction.reference,
                    provider=self.provider_name(),
                    status=TransactionStatus.PENDING,
                    amount=transaction.amount,
                    currency=transaction.currency,
                    payment_link=data.get("redirect_url"),
                    transaction_token=data.get("client_token"),
                    metadata=data,
                    raw_response=data,
                )

            raise PaymentError(
                message=f"Klarna payment initiation failed with {response.status}",
                status_code=response.status,
                raw_response=data,
            )

    async def check_status(self, order_id: str) -> TransactionStatusResponse:
        """Check Klarna order status."""
        headers = await self.get_headers()
        async with self.get_client() as client:
            response = await client.get(f"/payments/v1/orders/{order_id}", headers=headers)
            data = getattr(response, "json", lambda: response.data)()

            if response.status in range(200, 300):
                status = self.get_normalize_status(data.get("status", "UNKNOWN"))
                return TransactionStatusResponse(
                    transaction_id=order_id,
                    provider=self.provider_name(),
                    status=status,
                    amount=float(data.get("order_amount", 0)) / 100,
                    data=data,
                )

            raise PaymentError(
                message=f"Klarna status check failed: {order_id}",
                status_code=response.status,
                raw_response=data,
            )

    async def refund(self, order_id: str, amount: Optional[float] = None) -> PaymentResponse:
        """Issue refund through Klarna."""
        headers = await self.get_headers()
        refund_data = {
            "refunded_amount": int((amount or 0) * 100),
            "description": "Refund via EasySwitch",
        }

        async with self.get_client() as client:
            response = await client.post(
                f"/payments/v1/orders/{order_id}/refunds",
                json_data=refund_data,
                headers=headers,
            )
            data = getattr(response, "json", lambda: response.data)()

            if response.status in range(200, 300):
                return PaymentResponse(
                    transaction_id=order_id,
                    reference=f"refund-{order_id}",
                    provider=self.provider_name(),
                    status=TransactionStatus.REFUNDED,
                    amount=amount or float(data.get("refunded_amount", 0)) / 100,
                    currency=data.get("currency", "EUR"),
                    metadata=data,
                    raw_response=data,
                )

            raise PaymentError(
                message=f"Klarna refund failed with {response.status}",
                status_code=response.status,
                raw_response=data,
            )

    async def cancel_transaction(self, transaction_id: str) -> bool:
        """Cancel a Klarna order."""
        headers = await self.get_headers()
        async with self.get_client() as client:
            response = await client.post(
                f"/payments/v1/orders/{transaction_id}/cancel", headers=headers
            )
            if response.status in range(200, 300):
                return True

            raise PaymentError(
                message=f"Cancellation failed ({response.status})",
                status_code=response.status,
            )

    async def get_transaction_detail(self, transaction_id: str) -> TransactionDetail:
        """Retrieve Klarna order details."""
        headers = await self.get_headers()
        async with self.get_client() as client:
            response = await client.get(f"/payments/v1/orders/{transaction_id}", headers=headers)
            data = getattr(response, "json", lambda: response.data)()

            if response.status in range(200, 300):
                customer_info = data.get("billing_address", {})
                customer = CustomerInfo(
                    email=customer_info.get("email"),
                    phone_number=customer_info.get("phone"),
                    first_name=customer_info.get("given_name"),
                    last_name=customer_info.get("family_name"),
                )
                status = self.get_normalize_status(data.get("status", "UNKNOWN"))

                return TransactionDetail(
                    transaction_id=transaction_id,
                    provider=self.provider_name(),
                    amount=float(data.get("order_amount", 0)) / 100,
                    currency=data.get("purchase_currency", "EUR"),
                    status=status,
                    reference=data.get("order_id") or transaction_id,
                    created_at=datetime.utcnow(),
                    customer=customer,
                    metadata=data,
                    raw_data=data,
                )

            raise PaymentError(
                message=f"Failed to retrieve Klarna transaction {transaction_id}",
                status_code=response.status,
                raw_response=data,
            )
