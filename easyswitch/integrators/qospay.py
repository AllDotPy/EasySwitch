"""
EasySwitch - QosPay Integrator (stub).

This provider is not yet implemented. All operations raise
UnsupportedOperationError.
"""

from typing import Any, Dict, List, Optional

from easyswitch.adapters.base import AdaptersRegistry, BaseAdapter
from easyswitch.exceptions import UnsupportedOperationError
from easyswitch.types import (Currency, PaymentResponse, TransactionDetail,
                              TransactionStatus, TransactionStatusResponse,
                              WebhookEvent)


@AdaptersRegistry.register()
class QospayAdapter(BaseAdapter):
    """QosPay Adapter for EasySwitch SDK (placeholder)."""

    SANDBOX_URL: str = ""
    PRODUCTION_URL: str = ""

    SUPPORTED_CURRENCIES: List[Currency] = []

    def validate_credentials(self) -> bool:
        return False

    def get_credentials(self):
        return {}

    def get_headers(self, authorization=False) -> Dict[str, str]:
        return {}

    def format_transaction(self, data: TransactionDetail) -> Dict[str, Any]:
        raise UnsupportedOperationError("QosPay is not yet implemented")

    def get_normalize_status(self, status: str) -> TransactionStatus:
        return TransactionStatus.UNKNOWN

    async def send_payment(self, transaction: TransactionDetail) -> PaymentResponse:
        raise UnsupportedOperationError("QosPay is not yet implemented")

    async def check_status(self, transaction_id: str) -> TransactionStatusResponse:
        raise UnsupportedOperationError("QosPay is not yet implemented")

    async def cancel_transaction(self, transaction_id: str) -> bool:
        raise UnsupportedOperationError("QosPay is not yet implemented")

    async def refund(self, transaction_id: str, amount: Optional[float] = None,
                     reason: Optional[str] = None) -> PaymentResponse:
        raise UnsupportedOperationError("QosPay is not yet implemented")

    async def validate_webhook(self, payload: Dict[str, Any],
                               headers: Dict[str, str]) -> bool:
        raise UnsupportedOperationError("QosPay is not yet implemented")

    async def parse_webhook(self, payload: Dict[str, Any],
                            headers: Dict[str, str]) -> WebhookEvent:
        raise UnsupportedOperationError("QosPay is not yet implemented")

    async def get_transaction_detail(self, transaction_id: str) -> TransactionDetail:
        raise UnsupportedOperationError("QosPay is not yet implemented")
