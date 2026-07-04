"""
EasySwitch - MTN Mobile Money Integrator
"""
import base64
import hashlib
import hmac
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, ClassVar, Dict, List, Optional

from easyswitch.adapters.base import AdaptersRegistry, BaseAdapter
from easyswitch.exceptions import (APIError, AuthenticationError,
                                   TransactionNotFoundError,
                                   UnsupportedOperationError)
from easyswitch.types import (Currency, CustomerInfo, PaymentResponse,
                              Provider, TransactionDetail, TransactionStatus,
                              TransactionStatusResponse, WebhookEvent)


####
##      MTN MOBILE MONEY INTEGRATOR
#####
@AdaptersRegistry.register()
class MTNAdapter(BaseAdapter):
    """MTN Mobile Money Adapter for EasySwitch SDK."""

    SANDBOX_URL: str = "https://sandbox.momodeveloper.mtn.com"
    PRODUCTION_URL: str = "https://proxy.momoapi.mtn.com"

    SUPPORTED_CURRENCIES: ClassVar[List[Currency]] = [
        Currency.XOF,
        Currency.XAF,
        Currency.UGX,
        Currency.TZS,
        Currency.KES,
        Currency.RWF,
        Currency.ZMW,
        Currency.MWK,
        Currency.BIF,
        Currency.ETB,
        Currency.BWP,
        Currency.ZWL,
    ]

    MIN_AMOUNT: ClassVar[Dict[Currency, float]] = {
        Currency.XOF: 50.0,
        Currency.XAF: 50.0,
        Currency.UGX: 500.0,
        Currency.TZS: 500.0,
        Currency.KES: 10.0,
        Currency.RWF: 100.0,
        Currency.ZMW: 1.0,
        Currency.MWK: 100.0,
        Currency.BIF: 100.0,
        Currency.ETB: 1.0,
        Currency.BWP: 1.0,
        Currency.ZWL: 1.0,
    }

    def validate_credentials(self) -> bool:
        """Validate that MTN API credentials are present."""
        return all([
            self.config.api_key,
            self.config.api_secret,
            self.config.extra.get("app_id"),
        ])

    def get_credentials(self):
        """Return API credentials."""
        return {
            "api_key": self.config.api_key,
            "api_secret": self.config.api_secret,
            "app_id": self.config.extra.get("app_id", ""),
        }

    def get_headers(self, authorization=False) -> Dict[str, str]:
        """Return base headers for MTN requests."""
        headers = {
            "Ocp-Apim-Subscription-Key": self.config.api_key,
            "Content-Type": "application/json",
        }
        if authorization and self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        return headers

    def __init__(self, config, context=None):
        self._auth_token = None
        self._token_expires_at = None
        super().__init__(config, context)

    async def _ensure_auth_token(self) -> str:
        """
        Return a valid OAuth2 token, requesting a new one if expired.
        """

        now = datetime.now()

        if self._auth_token and self._token_expires_at and self._token_expires_at > now:
            return self._auth_token

        # Build Basic auth header from app_id and api_secret
        creds = self.get_credentials()
        basic_token = base64.b64encode(
            f"{creds['app_id']}:{creds['api_secret']}".encode()
        ).decode()

        async with self.get_client() as client:
            response = await client.post(
                endpoint="collection/token/",
                params={"grant_type": "client_credentials"},
                headers={
                    "Authorization": f"Basic {basic_token}",
                    "Content-Type": "application/json",
                }
            )

            if response.status not in range(200, 300):
                raise AuthenticationError(
                    message="MTN authentication failed",
                    status_code=response.status,
                    raw_response=response.data,
                )

            self._auth_token = response.data.get("access_token")
            if not self._auth_token:
                raise AuthenticationError("MTN authentication token not received")

            expires_in = int(response.data.get("expires_in", 3600))
            self._token_expires_at = now + timedelta(seconds=expires_in - 60)

            return self._auth_token

    def format_transaction(self, transaction: TransactionDetail) -> Dict[str, Any]:
        """Convert standardized TransactionDetail into MTN-specific payload."""

        clean_phone = transaction.customer.phone_number.replace("+", "").replace(" ", "")

        return {
            "amount": str(transaction.amount),
            "currency": transaction.currency,
            "externalId": transaction.reference or str(uuid.uuid4()),
            "payer": {
                "partyIdType": "MSISDN",
                "partyId": clean_phone,
            },
            "payerMessage": transaction.reason or "Payment via EasySwitch",
            "payeeNote": transaction.reason or "Payment via EasySwitch",
            "metadata": transaction.metadata or {},
        }

    async def send_payment(self, transaction: TransactionDetail) -> PaymentResponse:
        """
        Send an MTN Mobile Money payment request.
        """

        auth_token = await self._ensure_auth_token()
        payload = self.format_transaction(transaction)
        transaction_id = str(uuid.uuid4())

        async with self.get_client() as client:
            response = await client.post(
                endpoint="collection/v1_0/requesttopay",
                json_data=payload,
                headers={
                    **self.get_headers(authorization=True),
                    "X-Reference-Id": transaction_id,
                    "X-Callback-Url": (
                        transaction.callback_url
                        or self.config.callback_url
                        or ""
                    ),
                }
            )

            # MTN returns 202 Accepted — status must be polled separately.
            return PaymentResponse(
                transaction_id=transaction_id,
                provider=Provider.MTN,
                status=TransactionStatus.PENDING,
                amount=transaction.amount,
                currency=transaction.currency,
                reference=payload["externalId"],
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(minutes=10),
                customer=transaction.customer,
                metadata=transaction.metadata or {},
                raw_response=response.data if response.data else {},
            )

    async def check_status(self, transaction_id: str) -> TransactionStatusResponse:
        """
        Check the status of an MTN transaction.
        """

        auth_token = await self._ensure_auth_token()

        async with self.get_client() as client:
            response = await client.get(
                endpoint=f"collection/v1_0/requesttopay/{transaction_id}",
                headers=self.get_headers(authorization=True),
            )

            data = response.data or {}
            mtn_status = (data.get("status") or "").lower()

            status_mapping = {
                "pending": TransactionStatus.PENDING,
                "successful": TransactionStatus.SUCCESSFUL,
                "failed": TransactionStatus.FAILED,
                "cancelled": TransactionStatus.CANCELLED,
                "ongoing": TransactionStatus.PROCESSING,
                "rejected": TransactionStatus.FAILED,
                "timeout": TransactionStatus.EXPIRED,
            }

            return TransactionStatusResponse(
                transaction_id=transaction_id,
                provider=Provider.MTN,
                status=status_mapping.get(mtn_status, TransactionStatus.PENDING),
                amount=float(data.get("amount", 0)),
                data=data,
            )

    async def cancel_transaction(self, transaction_id: str) -> bool:
        """
        Cancel an MTN transaction.
        """
        raise UnsupportedOperationError(
            message="Transaction cancellation is not supported by MTN Mobile Money",
            provider=self.provider_name(),
        )

    async def refund(
        self,
        transaction_id: str,
        amount: Optional[float] = None,
        reason: Optional[str] = None,
    ) -> PaymentResponse:
        """
        Perform a refund (disbursement) for a completed MTN transaction.
        """

        auth_token = await self._ensure_auth_token()

        # Fetch the original transaction to verify it succeeded
        status_response = await self.check_status(transaction_id)
        if status_response.status != TransactionStatus.SUCCESSFUL:
            raise APIError(
                message=f"Cannot refund an unsuccessful transaction (status: {status_response.status})",
                provider="mtn",
            )

        async with self.get_client() as client:
            # Fetch original transaction detail
            detail_response = await client.get(
                endpoint=f"collection/v1_0/requesttopay/{transaction_id}",
                headers=self.get_headers(authorization=True),
            )

            detail_data = detail_response.data or {}
            original_amount = float(detail_data.get("amount", 0))
            payer_id = detail_data.get("payer", {}).get("partyId")
            currency = detail_data.get("currency", "XOF")

            refund_amount = amount if amount else original_amount
            if refund_amount > original_amount:
                raise ValueError(
                    f"Refund amount ({refund_amount}) cannot exceed "
                    f"original amount ({original_amount})"
                )

            refund_id = str(uuid.uuid4())

            refund_payload = {
                "amount": str(refund_amount),
                "currency": currency,
                "externalId": f"refund-{transaction_id}",
                "payee": {
                    "partyIdType": "MSISDN",
                    "partyId": payer_id,
                },
                "payerMessage": reason or "Refund via EasySwitch",
                "payeeNote": reason or "Refund via EasySwitch",
            }

            await client.post(
                endpoint="disbursement/v1_0/transfer",
                json_data=refund_payload,
                headers={
                    **self.get_headers(authorization=True),
                    "X-Reference-Id": refund_id,
                    "X-Callback-Url": self.config.callback_url or "",
                },
            )

            return PaymentResponse(
                transaction_id=refund_id,
                provider=Provider.MTN,
                status=TransactionStatus.PENDING,
                amount=refund_amount,
                currency=Currency(currency),
                reference=f"refund-{transaction_id}",
                created_at=datetime.now(),
                raw_response=detail_data,
            )

    async def validate_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str],
    ) -> bool:
        """
        Validate an incoming MTN webhook using HMAC-SHA256.
        """

        token = headers.get("X-Notification-Token") or headers.get("x-notification-token")
        if not token:
            return False

        expected = hmac.new(
            self.config.api_secret.encode(),
            json.dumps(payload, separators=(",", ":"), sort_keys=True).encode(),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, token)

    async def parse_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str],
    ) -> WebhookEvent:
        """
        Parse an MTN webhook into a standard WebhookEvent.
        """

        if not await self.validate_webhook(payload, headers):
            raise AuthenticationError(
                message="Invalid MTN webhook signature",
                provider=self.provider_name(),
            )

        transaction_id = payload.get("referenceId", "")
        status_str = (payload.get("status") or "").lower()

        status_mapping = {
            "successful": TransactionStatus.SUCCESSFUL,
            "failed": TransactionStatus.FAILED,
            "rejected": TransactionStatus.FAILED,
            "timeout": TransactionStatus.EXPIRED,
            "pending": TransactionStatus.PENDING,
            "ongoing": TransactionStatus.PROCESSING,
        }

        return WebhookEvent(
            event_type=payload.get("event", status_str),
            provider=Provider.MTN,
            transaction_id=transaction_id,
            status=status_mapping.get(status_str, TransactionStatus.PENDING),
            amount=float(payload.get("amount", 0)),
            currency=payload.get("currency", "XOF"),
            created_at=payload.get("created_at"),
            raw_data=payload,
            metadata=payload.get("metadata", {}),
        )

    async def get_transaction_detail(self, transaction_id: str) -> TransactionDetail:
        """
        Retrieve full transaction details from MTN.
        """

        auth_token = await self._ensure_auth_token()

        async with self.get_client() as client:
            response = await client.get(
                endpoint=f"collection/v1_0/requesttopay/{transaction_id}",
                headers=self.get_headers(authorization=True),
            )

            data = response.data or {}
            mtn_status = (data.get("status") or "").lower()

            status_mapping = {
                "pending": TransactionStatus.PENDING,
                "successful": TransactionStatus.SUCCESSFUL,
                "failed": TransactionStatus.FAILED,
                "cancelled": TransactionStatus.CANCELLED,
                "ongoing": TransactionStatus.PROCESSING,
                "rejected": TransactionStatus.FAILED,
                "timeout": TransactionStatus.EXPIRED,
            }

            return TransactionDetail(
                transaction_id=transaction_id,
                provider=Provider.MTN,
                amount=float(data.get("amount", 0)),
                currency=Currency(data.get("currency", "XOF")),
                status=status_mapping.get(mtn_status, TransactionStatus.UNKNOWN),
                reference=data.get("externalId"),
                raw_data=data,
            )

    def get_normalize_status(self, status: str) -> TransactionStatus:
        """Map MTN status strings to standardised TransactionStatus values."""

        mapping = {
            "pending": TransactionStatus.PENDING,
            "successful": TransactionStatus.SUCCESSFUL,
            "failed": TransactionStatus.FAILED,
            "cancelled": TransactionStatus.CANCELLED,
            "ongoing": TransactionStatus.PROCESSING,
            "rejected": TransactionStatus.FAILED,
            "timeout": TransactionStatus.EXPIRED,
        }
        return mapping.get(status.lower(), TransactionStatus.UNKNOWN)
