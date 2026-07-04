"""
EasySwitch - PayGate Global Integrator
"""
import hashlib
import hmac
import json
from typing import Any, ClassVar, Dict, List, Optional

from easyswitch.adapters.base import AdaptersRegistry, BaseAdapter
from easyswitch.conf.base import ProviderConfig
from easyswitch.exceptions import (AuthenticationError, InvalidProviderError, PaymentError,
                                   UnsupportedOperationError)
from easyswitch.types import (Currency, CustomerInfo, PaymentResponse,
                              Provider, TransactionDetail, TransactionStatus,
                              TransactionStatusResponse, TransactionType,
                              WebhookEvent)
from typing import Union

####
##      PAYGATE INTEGRATOR
#####
@AdaptersRegistry.register()
class PayGateAdapter(BaseAdapter):
    """PayGate Global Integrator for EasySwitch SDK."""
    SANDBOX_URL: str = "https://paygateglobal.com"
    PRODUCTION_URL: str = "https://paygateglobal.com"

    ENDPOINTS: Dict[str, str] = {
        "direct_payment": "/api/v1/pay",
        "payment": "/v1/page",
        "status_check": "/api/v1/status",
        "alt_status_check": "/api/v2/status",
        "balance_check": "/api/v1/check-balance"
    }

    SUPPORTED_CURRENCIES: ClassVar[List[Currency]] = [
        Currency.XOF
    ]

    MIN_AMOUNT: ClassVar[Dict[Currency, float]] = {
        Currency.XOF: 100.0
    }

    MAX_AMOUNT: ClassVar[Dict[Currency, float]] = {
        Currency.XOF: 1000000.0
    }

    # Mapping of supported mobile networks
    SUPPORTED_NETWORKS: ClassVar[List[str]] = ["FLOOZ", "TMONEY"]

    def get_credentials(self) -> Dict[str, str]:
        """Get PayGate credentials (just API key in this case)"""
        return {
            "api_key": self.config.api_key,
        }


    def validate_credentials(self) -> bool:
        """Validate credentials """
        return bool(self.config.api_key)



    def map_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map PayGate fields to standard transaction fields
        Args:
            data: Raw response data from PayGate API
        Returns:
            Standardized field mapping
        """
        field_mapping = {
            "transaction_id": "identifier",
            "reference": "tx_reference",
            "amount": "amount",
            "currency": "currency",
            "status": "status",
            "payment_method": "network"
        }

        return {standard: data.get(paygate) for standard, paygate in field_mapping.items()}

    def validate_transaction(self, transaction: TransactionDetail) -> bool:
        if transaction.currency not in self.SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency: {transaction.currency}")

        min_amount = self.MIN_AMOUNT.get(transaction.currency, 0)
        if transaction.amount < min_amount:
            raise ValueError(f"Amount too small. Minimum: {min_amount}")

        return True


    def get_headers(self, authorization: bool = False) -> Dict[str, str]:
        """Get headers for PayGate API requests."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        return headers

    def format_transaction(self, data: TransactionDetail) -> Dict[str, Any]:
        """Format transaction data for PayGate API."""
        self.validate_transaction(data)

        # PayGate expects amount without decimals for XOF
        amount = int(data.amount) if data.currency == Currency.XOF else data.amount

        order = {
            "auth_token": self.config.api_key,
            "phone_number": data.customer.phone_number.replace(" ", ""),
            "amount": amount,
            "description": data.reason or "Payment",
            "identifier": data.transaction_id,
            "network": data.provider.name or "FLOOZ"  # Default to FLOOZ
        }

        # Add optional parameters
        # if data.callback_url:
        #     order["callback_url"] = data.callback_url

        return order

    def get_normalize_status(self, status_code: str) -> TransactionStatus:
        """Normalize PayGate status codes to our standard."""
        status_mapping = {
            "0": TransactionStatus.SUCCESSFUL,  # Payment successful
            "2": TransactionStatus.PENDING,     # Invalid authentication token
            "4": TransactionStatus.EXPIRED,     # Invalid parameters
            "6": TransactionStatus.CANCELLED    # Duplicate detected. A transaction with the same identifier already exists.
        }
        return status_mapping.get(str(status_code), TransactionStatus.UNKNOWN)

    async def direct_payment(self, transaction: TransactionDetail) -> PaymentResponse:
        """
        Initiate payment using PayGate's direct API method.

        Documentation: Method 12 in the guide
        """
        payload = self.format_transaction(transaction)

        async with self.get_client() as client:
            response = await client.post(
                endpoint=self.ENDPOINTS["direct_payment"],
                json_data=payload,
                headers=self.get_headers()
            )

        if response.status in range(200, 300):
            return PaymentResponse(
                transaction_id=payload["identifier"],
                provider=transaction.provider.name,
                status=self.get_normalize_status(str(response.data.get("status"))),
                amount=payload["amount"],
                currency=transaction.currency,
                reference=response.data.get("tx_reference"),
                payment_link=None,  # No link for direct method
                transaction_token=None,
                customer=transaction.customer,
                raw_response=response.data,
                metadata=transaction.metadata
            )

        raise PaymentError(
            message=f"Payment failed: {response.data.get('message', 'Unknown error')}",
            status_code=response.status,
            raw_response=response.data
        )

    async def send_payment(self, transaction: TransactionDetail) -> PaymentResponse:
        """
        Create a PayGate payment page link (Method 2 in documentation).

        Returns a PaymentResponse with the payment_link set.
        """
        params = {
            "token": self.config.api_key,
            "amount": int(transaction.amount),  # PayGate expects an integer for XOF
            "description": transaction.reason or "Payment",
            "identifier": transaction.transaction_id
        }

        # Optional parameters
        if transaction.callback_url:
            params["url"] = transaction.callback_url
        if transaction.customer.phone_number:
            params["phone"] = transaction.customer.phone_number.replace(" ", "")
        if transaction.provider.name:
            params["network"] = transaction.provider.name

        payment_url = f"{self.PRODUCTION_URL}{self.ENDPOINTS['payment']}?{self._dict_to_query(params)}"

        return PaymentResponse(
            transaction_id=transaction.transaction_id,
            provider=transaction.provider.name,
            status=TransactionStatus.PENDING,
            amount=transaction.amount,
            currency=transaction.currency,
            reference=transaction.transaction_id,  # Use transaction ID as temporary reference
            payment_link=payment_url,
            transaction_token=None,
            customer=transaction.customer,
            raw_response={"payment_url": payment_url},
            metadata=transaction.metadata
        )

    async def check_status(self, transaction_id: str) -> TransactionStatusResponse:
        """
        Check transaction status using either reference method.

        Documentation: "Check Payment Status"
        """
        # Try first with v2 method (by identifier)
        async with self.get_client() as client:
            response = await client.post(
                endpoint=self.ENDPOINTS["alt_status_check"],
                json_data={
                    "auth_token": self.config.api_key,
                    "identifier": transaction_id
                },
                headers=self.get_headers()
            )

            if response.status in range(200, 300):
                data = response.data
                return TransactionStatusResponse(
                    transaction_id=transaction_id,
                    provider=self.provider_name(),
                    status=self.get_normalize_status(data.get("status")),
                    amount=float(data.get("amount", 0)),
                    data=data
                )

        # If v2 method fails, try with v1 method (requires tx_reference)
        raise PaymentError(
            message="Status check failed. Note: v1 API requires tx_reference, not transaction_id.",
            status_code=response.status,
            raw_response=response.data
        )

    async def get_transaction_detail(self, transaction_id: str) -> TransactionDetail:
        """Get transaction details - PayGate doesn't support this directly"""
        # On utilise check_status comme alternative
        status_response = await self.check_status(transaction_id)

        return TransactionDetail(
            transaction_id=transaction_id,
            provider=self.provider_name(),
            amount=status_response.amount,
            currency=Currency.XOF,
            reference=status_response.data.get("tx_reference", ""),
            customer=CustomerInfo(),
            status=status_response.status,
            created_at=status_response.data.get('datetime'),
            transaction_type=TransactionType.PAYMENT,
            raw_data=status_response.data
        )
    def validate_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> bool:
        """
        Validate PayGate webhook signature.

        Documentation: "Receive Payment Confirmation"
        """
        if not payload or not headers:
            return False

        # PayGate doesn't use HMAC signature in webhooks,
        # but we validate that required fields are present
        required_fields = ["tx_reference", "identifier", "amount", "status"]
        if not all(field in payload for field in required_fields):
            return False

        return True

    def parse_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> WebhookEvent:
        """Parse PayGate webhook payload."""
        if not self.validate_webhook(payload, headers):
            raise AuthenticationError(
                message="Invalid webhook payload",
                provider=self.provider_name()
            )

        return WebhookEvent(
            event_type="payment_" + payload["status"].lower(),
            provider=self.provider_name(),
            transaction_id=payload["identifier"],
            amount=float(payload["amount"]),
            currency=Currency.XOF,  # PayGate works in XOF
            created_at=payload.get("datetime"),
            raw_data=payload
        )

    async def get_balance(self) -> Dict[str, float]:
        """
        Check account balances (FLOOZ and TMONEY).

        Documentation: "Check Your Balance"
        Note: Requires IP whitelisting on PayGate side
        """
        async with self.get_client() as client:
            response = await client.post(
                endpoint=self.ENDPOINTS["balance_check"],
                json_data={"auth_token": self.config.api_key},
                headers=self.get_headers()
            )

        if response.status in range(200, 300):
            return {
                "flooz": float(response.data.get("flooz", 0)),
                "tmoney": float(response.data.get("tmoney", 0))
            }

        raise PaymentError(
            message="Failed to get balance",
            status_code=response.status,
            raw_response=response.data
        )

    async def refund(self, transaction_id: str, amount: Optional[float] = None) -> PaymentResponse:
        """Refund is not directly supported via API according to documentation."""
        raise UnsupportedOperationError(
            message="PayGate does not support API refunds. Use dashboard instead.",
            provider=self.provider_name()
        )

    async def cancel_transaction(self, transaction_id: str) -> None:
        """Cancellation not supported via API."""
        raise UnsupportedOperationError(
            message="Transaction cancellation must be done manually in PayGate dashboard",
            provider=self.provider_name()
        )

    def _dict_to_query(self, params: Dict[str, Any]) -> str:
        """Convert dictionary to URL query string."""
        return "&".join(f"{k}={v}" for k, v in params.items())

    @classmethod
    def provider_name(cls) -> str:
        return "PAYGATE"
