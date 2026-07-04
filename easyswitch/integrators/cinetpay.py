"""
EasySwitch - CinetPay Integrator
"""
import hashlib
import hmac
import json
from typing import Any, ClassVar, Dict, List, Optional

from easyswitch.adapters.base import AdaptersRegistry, BaseAdapter
from easyswitch.exceptions import (AuthenticationError, PaymentError,
                                   UnsupportedOperationError)
from easyswitch.types import (Currency, CustomerInfo, PaymentResponse,
                              Provider, TransactionDetail, TransactionStatus,
                              TransactionStatusResponse, TransactionType,
                              WebhookEvent)


####
##      CINETPAY INTEGRATOR
#####
@AdaptersRegistry.register()
class CinetpayAdapter(BaseAdapter):
    """CinetPay Integrator for EasySwitch SDK."""

    SANDBOX_URL: str = "https://api-checkout.cinetpay.com"

    PRODUCTION_URL: str = "https://api-checkout.cinetpay.com"

    ENDPOINTS: Dict[str, str] = {
        "payment": "/v2/payment",
        "payment_status": "/v2/payment/check",
    }

    SUPPORTED_CURRENCIES: ClassVar[List[Currency]] = [
        Currency.XOF,
        Currency.XAF,
        Currency.CDF,
        Currency.GNF,
        Currency.USD
    ]

    MIN_AMOUNT: ClassVar[Dict[Currency, float]] = {
        Currency.XOF: 100.0,
        Currency.XAF: 100.0,
        Currency.CDF: 1000.0,
        Currency.GNF: 1000.0,
        Currency.USD: 1.0
    }

    MAX_AMOUNT: ClassVar[Dict[Currency, float]] = {     # Currently unknown
        Currency.XOF: 1000000.0,
        Currency.XAF: 1000000.0,
        Currency.CDF: 1000000.0,
        Currency.GNF: 1000000.0,
        Currency.USD: 10000.0
    }

    def validate_credentials(self) -> bool:
        """ Validate the credentials for CinetPay. """
        
        return all([
            self.config.api_key, 
            self.config.extra,                  # Extra configs must be set
            self.config.extra.get("site_id"),   # CinetPay uses SITE_ID 
            self.config.extra.get("secret"),    # and secret key (token)
        ])
    
    def get_credentials(self):
        """Get the credentials for CinetPay."""
        # NOTE that credentials are checked in the constructor

        return {
            "api_key": self.config.api_key,
            "site_id": self.config.extra.get('site_id','')
        }
            
    def get_headers(self, authorization=False):
        """Get the headers for CinetPay."""

        headers = {
            'Content-Type':'application/json'
        }
       
        return headers
    
    def format_transaction(self, data: TransactionDetail) -> Dict[str, Any]:
        """Format the transaction data into a standardized format."""

        # Check if the transaction is valid
        self.validate_transaction(data)     # Will raise ValidationError if needed.

        order = self.get_credentials()
        order |= {
            "amount": int(data.amount),                     # For security
            "transaction_id": data.transaction_id,
            "currency": data.currency,
            "description": data.reason,
            "customer_id": data.customer.id,
            "customer_name": data.customer.last_name,
            "customer_surname": data.customer.first_name,
            "customer_email": data.customer.email,
            "customer_phone": data.customer.phone_number.replace(" ", "").lstrip("+"),
            "customer_country": data.customer.country,
            "customer_state": data.customer.state,
            "customer_city": data.customer.city,
            "customer_zip_code": data.customer.zip_code,
            "customer_address": data.customer.address,
            "reference": data.reference,
            "notify_url": data.callback_url or self.config.callback_url,
            "return_url": data.return_url or self.config.callback_url,
            "channels": self.config.extra.get("channels","MOBILE_MONEY"),              # ALWAYS MOBILE MONEY SINCE WE ONLY SUPPORT MOBILE MONEY
            "metadata": json.dumps(data.metadata)
        }
        return order
    
    def get_normalize_status(self, status):
        """ Normalize the status of a transaction. """

        # CinetPay uses the following statuses
        statues = {
            # Success statuses
            "SUCCESS": TransactionStatus.SUCCESSFUL,
            # Pending statuses
            "CREATED": TransactionStatus.PENDING,
            "PENDING": TransactionStatus.PENDING,
            "WAITING_CUSTOMER_TO_VALIDATE": TransactionStatus.PENDING,
            "WAITING_CUSTOMER_PAYMENT": TransactionStatus.PENDING,
            "WAITING_CUSTOMER_OTP_CODE": TransactionStatus.PENDING,
            # Failed statuses
            "PAYMENT_FAILED": TransactionStatus.FAILED,
            "INSUFFICIENT_BALANCE": TransactionStatus.FAILED,
            # Error statuses
            "OTP_CODE_ERROR": TransactionStatus.ERROR,
            "MINIMUM_REQUIRED_FIELDS": TransactionStatus.ERROR,
            "INVALID_TRANSACTION": TransactionStatus.ERROR,
            "AUTH_NOT_FOUND": TransactionStatus.ERROR,
            # Expired statuses
            "ABONNEMENT_OR_TRANSACTIONS_EXPIRED": TransactionStatus.EXPIRED,
            # Cancelled statuses
            "TRANSACTION_CANCEL": TransactionStatus.CANCELLED,
            "REFUSED": TransactionStatus.REFUSED
        }
        return statues.get(status, TransactionStatus.UNKNOWN)
    
    def get_payload_str(self, payload: Dict[str, Any]) -> str:
        """ Get the payload as a string. """
        # We need to convert the payload to a string
        # in the following format as specified by the API's documentation.
        # cpm_site_id + cpm_trans_id + cpm_trans_date + cpm_amount + cpm_currency + signature + 
        # payment_method + cel_phone_num + cpm_phone_prefixe + cpm_language + cpm_version 
        # + cpm_payment_config + cpm_page_action + cpm_custom + cpm_designation + cpm_error_message

        return (
            f"{payload.get('cpm_site_id')}{payload.get('cpm_trans_id')}"
            f"{payload.get('cpm_trans_date')}{payload.get('cpm_amount')}"
            f"{payload.get('cpm_currency')}{payload.get('signature')}"
            f"{payload.get('payment_method')}{payload.get('cel_phone_num')}"
            f"{payload.get('cpm_phone_prefixe')}{payload.get('cpm_language')}"
            f"{payload.get('cpm_version')}{payload.get('cpm_payment_config')}"
            f"{payload.get('cpm_page_action')}{payload.get('cpm_custom')}"
            f"{payload.get('cpm_designation')}{payload.get('cpm_error_message')}"
        ) 
    
    def compare_tokens(self, payload_str: str, recieved_token: str) -> bool:
        """ Compare the tokens. """

        # First generate the token from the payload string
        token = hmac.new(
            key = self.config.extra.get("secret","").encode(),
            msg = payload_str.encode(),
            digestmod = hashlib.sha256
        ).hexdigest()

        # Then compare the tokens
        return hmac.compare_digest(
            token,
            recieved_token
        )

    def validate_webhook(self, payload, headers) -> bool:
        """ Validate the webhook payload. """
        if not payload:
            return False
        
        if not headers or 'x-token' not in headers:
            return False
        
        recieved_token = headers.get('x-token')
        data = self.get_payload_str(payload)
        
        return self.compare_tokens(data, recieved_token)
    
    def parse_webhook(self, payload, headers):
        """ Parse the webhook payload. """
        # Check if the payload is valid
        if not self.validate_webhook(payload, headers):
            raise AuthenticationError(
                message="Invalid webhook signature",
                provider = self.provider_name()
            )
        
        # Derive status from the payment action
        action = payload.get("cpm_page_action", "")
        event_status = (
            TransactionStatus.SUCCESSFUL
            if "SUCCESS" in action.upper()
            else TransactionStatus.UNKNOWN
        )

        return WebhookEvent(
            event_type = action,
            provider = self.provider_name(),
            transaction_id = payload.get("cpm_trans_id"),
            status = event_status,
            amount = payload.get("cpm_amount"),
            currency = payload.get("cpm_currency"),
            created_at = payload.get("cpm_trans_date"),
            raw_data = payload
        )
    
    async def send_payment(
        self, 
        transaction: TransactionDetail
    ) -> PaymentResponse:
        """
        Send a payment request to CinetPay.
        """
        # First we need to format the transaction
        order = self.format_transaction(transaction)

        # Then send the payment request
        async with self.get_client() as client:
            response = await client.post(
                endpoint = self.ENDPOINTS["payment"],
                json_data = order,
                headers = self.get_headers()
            )

            # Check if the response is successful
            if response.status in range(200, 300):
                # Extract the payment link from the response
                payment_link = response.data.get("data",{}).get("payment_url")

                # Create a PaymentResponse object
                return PaymentResponse(
                    transaction_id = order.get("transaction_id"),
                    provider = self.provider_name(),
                    status = TransactionStatus.PENDING,
                    amount = order["amount"],
                    currency = order["currency"],
                    reference = order["reference"],
                    payment_link = payment_link,
                    transaction_token = response.data.get("data").get("payment_token"),
                    customer = transaction.customer,
                    raw_response = response.data,
                    metadata = transaction.metadata
                )
            
            # If the response is not successful, raise an API error
            raise PaymentError(
                message = "Payment request failed",
                status_code = response.status,
                raw_response = response.data
            )
    
    async def check_status(self, transaction_id: str) -> TransactionStatusResponse:
        """
        Check the status of a transaction.
        """
        # Send a GET request to check the status of the transaction
        async with self.get_client() as client:
            response = await client.post(
                endpoint = self.ENDPOINTS["payment_status"],
                json_data = {
                    "transaction_id": transaction_id,
                    **self.get_credentials()
                },
                headers = self.get_headers()
            )
            # No need to check the status code, cinetpay sends the status in the body
            # Check if the response is successful
            if response.status in range(200, 300):
                data = response.data
                # check for a success message
                status = data.get('message')

                return TransactionStatusResponse(
                    transaction_id = transaction_id,
                    provider = self.provider_name(),
                    status = self.get_normalize_status(status),
                    amount = data.get("data").get("amount"),
                    data = data
                )
            
            # If the response is not successful, raise an API error
            raise PaymentError(
                message = (
                    f"Payment request failed with status {response.status}."
                    f"\n url: {response.url}"
                ),
                status_code = response.status,
                raw_response = response.data
            )
    
    async def cancel_transaction(self, transaction_id):
        """
        Cancel a transaction.
        """
        # CinetPay does not support transaction cancellation
        raise UnsupportedOperationError(
            message = "CinetPay does not support transaction cancellation",
            provider = self.provider_name()
        )
    
    async def refund(
        self, 
        transaction_id: str, 
        amount: Optional[float] = None
    ) -> PaymentResponse:
        """
        Refund a transaction.
        """
        # CinetPay does not support refunds
        raise UnsupportedOperationError(
            message = "CinetPay does not support refunds",
            provider = self.provider_name()
        )
    
    async def get_transaction_detail(self, transaction_id: str) -> TransactionDetail:
        """
        Get the details of a transaction.
        """
        # CinetPay does not support 
        raise UnsupportedOperationError(
            message = (
                "CinetPay does not allow to retrive transactions by id. "
                "Use check_status instead."
            ),
            provider = self.provider_name()
        )