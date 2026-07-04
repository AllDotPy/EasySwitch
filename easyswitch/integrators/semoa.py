
"""
EasySwitch - SEMOA Integrator
"""

from typing import Any, ClassVar, Dict, List, Optional

from easyswitch.adapters.base import AdaptersRegistry, BaseAdapter
from easyswitch.exceptions import (AuthenticationError, PaymentError,
                                   TransactionNotFoundError,
                                   UnsupportedOperationError)
from easyswitch.types import (Currency, CustomerInfo, PaymentResponse,
                              Provider, TransactionDetail, TransactionStatus,
                              TransactionStatusResponse, TransactionType,
                              WebhookEvent)


####
##      SEMOA INTEGRATOR
#####
@AdaptersRegistry.register()
class SemoaAdapter(BaseAdapter):
    """Semoa Integrator for EasySwitch SDK."""

    SANDBOX_URL: str = "https://sandbox.semoa-payments.com/api/"

    # TODO: Replace with actual production URL when available.
    PRODUCTION_URL: str = "https://sandbox.semoa-payments.com/api/"

    SUPPORTED_CURRENCIES: ClassVar[List[Currency]] = [
        Currency.XOF,
        Currency.XAF,
        Currency.EUR,
        Currency.USD
    ]

    MIN_AMOUNT: ClassVar[Dict[Currency, float]] = {
        Currency.XOF: 100.0,
        Currency.XAF: 100.0,
        Currency.EUR: 1.0,
        Currency.USD: 1.0
    }

    MAX_AMOUNT: ClassVar[Dict[Currency, float]] = {
        Currency.XOF: 1000000.0,
        Currency.XAF: 1000000.0,
        Currency.EUR: 10000.0,
        Currency.USD: 10000.0
    }

    def validate_credentials(self) -> bool:
        """Validate that all required Semoa credentials are present."""

        return all([
            self.config.api_key,
            self.config.extra.get('client_id'),
            self.config.extra.get('client_secret'),
            self.config.extra.get('username'),
            self.config.extra.get('password'),
            self.config.callback_url
        ])

    def get_credentials(self):
        """Get the credentials for Semoa."""
        return {
            "username": self.config.extra.get('username'),
            "password": self.config.extra.get('password'),
            "client_id": self.config.extra.get('client_id'),
            "client_secret": self.config.extra.get('client_secret'),
        }

    def get_headers(self, authorization=False):
        """Get the headers for Semoa."""

        headers = {
            'Content-Type': 'application/json'
        }
        if authorization:
            headers['Authorization'] = f'Bearer {self.config.token}'
        return headers

    async def authenticate(self):
        """Authenticate the application and retrieve a Semoa access token."""

        async with self.get_client() as client:
            response = await client.post(
                endpoint="auth",
                json_data=self.get_credentials(),
                headers={
                    "Content-Type": "application/json"
                }
            )
            if response.status == 200:
                self.config.token = response.data.get("access_token")
                return True
            else:
                raise AuthenticationError(
                    message="Authentication failed",
                    status_code=response.status,
                    raw_response=response.data
                )

    def format_transaction(self, data: TransactionDetail) -> Dict[str, Any]:
        """
        Convert standardized TransactionDetail into Semoa-specific order format.
        """

        self.validate_transaction(data)

        return {
            "amount": data.amount,
            "currency": data.currency,
            "description": data.reason,
            "client": {
                "last_name": data.customer.last_name or "Doe",
                "first_name": data.customer.first_name or "John",
                "phone": data.customer.phone_number.replace(" ", "")
            },
            "metadata": data.metadata,
            "callback_url": data.callback_url or self.config.callback_url
        }

    async def send_payment(self, transaction: TransactionDetail) -> PaymentResponse:
        """
        Send a payment request to Semoa.
        """

        order = self.format_transaction(transaction)

        async with self.get_client() as client:
            response = await client.post(
                endpoint="orders",
                json_data=order,
                headers=self.get_headers(authorization=True)
            )

            if response.status in range(200, 300):
                payment_link = response.data.get("bill_url")
                transaction_id = response.data.get("orderNum")

                return PaymentResponse(
                    transaction_id=transaction_id,
                    provider=self.provider_name(),
                    status=TransactionStatus.PENDING,
                    amount=transaction.amount,
                    currency=transaction.currency,
                    created_at=response.data.get("created_at"),
                    expires_at=response.data.get("expires_at"),
                    reference=response.data.get("reference"),
                    payment_link=payment_link,
                    customer=transaction.customer,
                    raw_response=response.data,
                    metadata=transaction.metadata
                )

            raise PaymentError(
                message="Payment request failed",
                status_code=response.status,
                raw_response=response.data
            )

    async def check_status(self, transaction_id: str) -> TransactionStatusResponse:
        """
        Check the status of a transaction.
        """

        async with self.get_client() as client:
            response = await client.get(
                endpoint=f"orders/{transaction_id}",
                headers=self.get_headers(authorization=True)
            )

            if response.status in range(200, 300):
                status = response.data.get("status")
                return TransactionStatusResponse(
                    transaction_id=transaction_id,
                    provider=self.provider_name(),
                    status=TransactionStatus(status) if status else TransactionStatus.UNKNOWN,
                    amount=response.data.get("amount", 0),
                    data=response.data,
                )

            raise TransactionNotFoundError(
                message="Transaction not found",
                status_code=response.status,
                raw_response=response.data
            )

    async def cancel_transaction(self, transaction_id: str) -> bool:
        """
        Cancel a transaction.
        """

        async with self.get_client() as client:
            response = await client.delete(
                endpoint=f"orders/{transaction_id}",
                headers=self.get_headers(authorization=True)
            )

            return response.status in range(200, 300)

    async def refund(
        self,
        transaction_id: str,
        amount: Optional[float] = None,
        reason: Optional[str] = None
    ) -> PaymentResponse:
        """
        Refund a transaction.
        """
        raise UnsupportedOperationError(
            message="Semoa does not support refunds via the public API",
            provider=self.provider_name()
        )

    async def validate_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> bool:
        """
        Validate an incoming Semoa webhook.
        Semoa sends a signature via an Authorization or X-Semoa-Signature header.
        """
        # TODO: Implement Semoa-specific webhook signature verification
        # when their webhook documentation is available.
        return True

    async def parse_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> WebhookEvent:
        """
        Parse a Semoa webhook into a standard WebhookEvent.
        """

        if not await self.validate_webhook(payload, headers):
            raise AuthenticationError(
                message="Invalid webhook signature",
                provider=self.provider_name()
            )

        return WebhookEvent(
            event_type=payload.get("event", payload.get("status", "unknown")),
            provider=self.provider_name(),
            transaction_id=str(payload.get("orderNum", payload.get("id", ""))),
            status=self.get_normalize_status(payload.get("status", "").upper()) if hasattr(self, 'get_normalize_status') else TransactionStatus.UNKNOWN,
            amount=float(payload.get("amount", 0)),
            currency=payload.get("currency", "XOF"),
            created_at=payload.get("created_at"),
            raw_data=payload,
            metadata=payload.get("metadata", {}),
        )

    async def get_transaction_detail(self, transaction_id: str) -> TransactionDetail:
        """
        Retrieve full transaction details from Semoa.
        Falls back to check_status enriched with minimal detail.
        """
        status_response = await self.check_status(transaction_id)

        return TransactionDetail(
            transaction_id=transaction_id,
            provider=self.provider_name(),
            amount=status_response.amount,
            currency=Currency.XOF,
            status=status_response.status,
            raw_data=status_response.data,
        )

    def get_normalize_status(self, status: str) -> TransactionStatus:
        """Map Semoa status strings to standardised TransactionStatus values."""

        mapping = {
            "PENDING": TransactionStatus.PENDING,
            "SUCCESSFUL": TransactionStatus.SUCCESSFUL,
            "SUCCESS": TransactionStatus.SUCCESSFUL,
            "FAILED": TransactionStatus.FAILED,
            "FAIL": TransactionStatus.FAILED,
            "CANCELLED": TransactionStatus.CANCELLED,
            "CANCEL": TransactionStatus.CANCELLED,
            "EXPIRED": TransactionStatus.EXPIRED,
            "ERROR": TransactionStatus.ERROR,
        }
        return mapping.get(status, TransactionStatus.UNKNOWN)
