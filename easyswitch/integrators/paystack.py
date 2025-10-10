"""
EasySwitch - Paystack Integrator
"""

import hmac
import hashlib
import json
from typing import ClassVar, List, Dict, Optional, Any
from datetime import datetime

from easyswitch.adapters.base import AdaptersRegistry, BaseAdapter
from easyswitch.types import (Currency, PaymentResponse, WebhookEvent,
                              TransactionDetail,TransactionStatusResponse,
                              CustomerInfo, TransactionStatus)
from easyswitch.exceptions import  PaymentError,UnsupportedOperationError


@AdaptersRegistry.register()
class PaystackAdapter(BaseAdapter):
    """Paystack Adapter for EasySwitch SDK."""
    
    SANDBOX_URL: str = "https://api.paystack.co"
    PRODUCTION_URL: str = "https://api.paystack.co"

    SUPPORTED_CURRENCIES: ClassVar[List[Currency]] = [
        Currency.NGN,
        Currency.GHS,
        Currency.USD,
    ]

    MIN_AMOUNT: ClassVar[Dict[Currency, float]] = {
        Currency.NGN: 50.0,    # 50.00 NGN (main units)
        Currency.GHS: 0.10,    # 0.10 GHS
        Currency.USD: 2.0,     # 2.00 USD
    }

    MAX_AMOUNT: ClassVar[Dict[Currency, float]] = {
        Currency.NGN: 10_000_000,
        Currency.GHS: 10_000_000,
        Currency.USD: 10_000_000,
    }

    def validate_credentials(self) -> bool:
        """Validate the credentials for Paystack."""
        return bool(self.config.api_key)

    def get_credentials(self):
        """Return API credentials."""
        return {"api_key": self.config.api_key}

    def get_headers(self, authorization=True, **kwargs) -> Dict[str, str]:
        """Return headers for Paystack requests."""
        headers = {"Content-Type": "application/json"}
        if authorization:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers
    
    def get_normalize_status(self, status: str) -> TransactionStatus:
        """Normalize Paystack transaction status."""
        mapping = {
            "success": TransactionStatus.SUCCESSFUL,
            "failed": TransactionStatus.FAILED,
            "abandoned": TransactionStatus.CANCELLED,
            "pending": TransactionStatus.PENDING,
            "refund": TransactionStatus.REFUNDED,
        }
        return mapping.get(status.lower(), TransactionStatus.UNKNOWN)

        # validate_webhook expects raw_body: bytes
    def validate_webhook(self, raw_body: bytes, headers: Dict[str, str]) -> bool:
        """Validate the authenticity of a Paystack webhook."""
        signature = headers.get("x-paystack-signature")
        secret_key = getattr(self.config, "api_key", None)
        if not signature or not secret_key:
            return False

        computed_sig = hmac.new(secret_key.encode("utf-8"), msg=raw_body, digestmod=hashlib.sha512).hexdigest()
        return hmac.compare_digest(computed_sig, signature)
    
    def parse_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> WebhookEvent:
        """Parse and validate a Paystack webhook."""

        # Convert payload to bytes for validation
        raw_body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        
        if not self.validate_webhook(raw_body, headers):
            raise PaymentError("Invalid webhook signature", raw_response=payload)

        data = payload.get("data", {})
        event_type = payload.get("event", "unknown_event")
        transaction_id = data.get("reference")
        status = self.get_normalize_status(data.get("status"))
        amount = (data.get("amount") or 0) / 100
        currency = data.get("currency", "NGN")
        metadata = data.get("metadata", {}) or {}
        context = {
            "customer_email": data.get("customer", {}).get("email"),
            "authorization": data.get("authorization", {}),
        }

        return WebhookEvent(
            event_type=event_type,
            provider=self.provider_name(),
            transaction_id=transaction_id,
            status=status,
            amount=amount,
            currency=currency,
            created_at=datetime.fromtimestamp(data.get("createdAt") / 1000) if data.get("createdAt") else None,
            raw_data=payload,
            metadata=metadata,
            context=context,
        )
    
    def format_transaction(self, transaction: TransactionDetail) -> Dict[str, Any]:
        """Convert standardized TransactionDetail into Paystack-specific payload."""
        self.validate_transaction(transaction) 
        return {
            "amount": int(transaction.amount * 100),  # Paystack expects kobo
            "email": transaction.customer.email,
            "reference": transaction.reference,
            "callback_url": transaction.callback_url or self.config.callback_url,
            "metadata": transaction.metadata or {},
        }
        
    async def send_payment(self, transaction: TransactionDetail) -> PaymentResponse:
        """Send a payment initialization request to Paystack."""
        payload = self.format_transaction(transaction)

        async with self.get_client() as client:
            response = await client.post(
                "/transaction/initialize",
                json_data=payload,
                headers=self.get_headers()
            )

            data = response.json() if hasattr(response, "json") else response.data
            if response.status in range(200, 300) and data.get("status"):
                init_data = data.get("data", {})
                return PaymentResponse(
                    transaction_id=transaction.transaction_id,
                    reference=init_data.get("reference"),
                    provider=self.provider_name(),
                    status="pending",
                    amount=transaction.amount,
                    currency=transaction.currency,
                    payment_link=init_data.get("authorization_url"),
                    transaction_token=init_data.get("access_code"),
                    metadata=init_data,
                    raw_response=data,
                )

            raise PaymentError(
                message=f"Payment request failed with status {response.status}",
                status_code=response.status,
                raw_response=data,
            )

    async def check_status(self, reference: str) -> TransactionStatusResponse:
        """Check the status of a Paystack transaction by reference."""
        async with self.get_client() as client:
            response = await client.get(
                f"/transaction/verify/{reference}",
                headers=self.get_headers()
            )

            data = response.json() if hasattr(response, "json") else response.data
            if not data.get("status"):
                raise PaymentError(
                    message="Failed to verify Paystack transaction",
                    raw_response=data
                )

            tx = data.get("data", {})
            return TransactionStatusResponse(
                transaction_id=tx.get("id"),
                provider=self.provider_name(),
                status=self.get_normalize_status(tx.get("status")),
                amount=(tx.get("amount") or 0) / 100,
                data=tx,
            )

    async def cancel_transaction(self, transaction_id: str) -> None:
        """Paystack does not support transaction cancellation.
            Use refund() for post-payment reversals.
        """
        raise UnsupportedOperationError(
            self.provider_name(),
        )

    async def refund(self, transaction_id: str, amount: Optional[float] = None) -> PaymentResponse:
        """Refund a Paystack transaction."""
        async with self.get_client() as client:
            payload = {"transaction": transaction_id}
            if amount:
                payload["amount"] = int(amount * 100)  

            response = await client.post("/refund", json_data=payload, headers=self.get_headers())

            data = response.json() if hasattr(response, "json") else response.data
            if response.status in range(200, 300) and data.get("status"):
                refund_data = data.get("data", {})
                return PaymentResponse(
                    transaction_id=transaction_id,
                    reference=refund_data.get("transaction", {}).get("reference", f"refund-{transaction_id}"),
                    provider=self.provider_name(),
                    status=self.get_normalize_status(refund_data.get("status")),
                    amount=(refund_data.get("amount") or (amount or 0)) / 100,
                    currency=refund_data.get("currency", "NGN"),
                    metadata=refund_data,
                    raw_response=data,
                )

            raise PaymentError(
                message=f"Refund failed with status {response.status}",
                status_code=response.status,
                raw_response=data,
            )
        
    async def get_transaction_detail(self, transaction_id: str) -> TransactionDetail:
        """Retrieve transaction details from Paystack by transaction ID."""
        async with self.get_client() as client:
            response = await client.get(f"/transaction/{transaction_id}", headers=self.get_headers())

            data = response.json() if hasattr(response, "json") else response.data
            if response.status in range(200, 300) and data.get("status"):
                tx = data.get("data", {})

                customer = CustomerInfo(
                    email=tx.get("customer", {}).get("email"),
                    phone_number=tx.get("customer", {}).get("phone"),
                    first_name=tx.get("customer", {}).get("first_name"),
                    last_name=tx.get("customer", {}).get("last_name"),
                    metadata=tx.get("customer", {}).get("metadata", {}),
                )

                return TransactionDetail(
                    transaction_id=str(tx.get("id", transaction_id)),
                    provider=self.provider_name(),
                    amount=(tx.get("amount") or 0) / 100,
                    currency=tx.get("currency", "NGN"),
                    status=self.get_normalize_status(tx.get("status")),
                    reference=tx.get("reference"),
                    callback_url=tx.get("callback_url"),
                    created_at=datetime.fromtimestamp(tx.get("createdAt") / 1000) if tx.get("createdAt") else datetime.now(),
                    updated_at=datetime.fromtimestamp(tx.get("updatedAt") / 1000) if tx.get("updatedAt") else None,
                    completed_at=datetime.fromtimestamp(tx.get("paidAt") / 1000) if tx.get("paidAt") else None,
                    customer=customer,
                    metadata=tx.get("metadata", {}),
                    raw_data=tx
                )

            raise PaymentError(
                message=f"Failed to retrieve transaction {transaction_id}",
                status_code=response.status,
                raw_response=data
            )
