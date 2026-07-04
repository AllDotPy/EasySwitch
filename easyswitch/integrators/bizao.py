"""
EasySwitch - Bizao Integrator
"""
import hashlib
import hmac
import json
import base64
import asyncio
from typing import Any, ClassVar, Dict, List, Optional

from easyswitch.utils.http import HTTPClient
from easyswitch.adapters.base import AdaptersRegistry, BaseAdapter
from easyswitch.exceptions import (AuthenticationError, PaymentError,
                                   UnsupportedOperationError)
from easyswitch.types import (Currency, CustomerInfo, PaymentResponse,
                              Provider, TransactionDetail, TransactionStatus,
                              TransactionStatusResponse, TransactionType,
                              WebhookEvent)
from easyswitch.utils import (
    dict_to_encoded_query_string, encoded_query_string_to_dict
)


####
##      BIZAO INTEGRATOR
#####
@AdaptersRegistry.register()
class BizaoAdapter(BaseAdapter):
    """Bizao Integrator for EasySwitch SDK."""

    SANDBOX_URL: str = "https://preproduction-gateway.bizao.com/mobilemoney"

    PRODUCTION_URL: str = "https://api.bizao.com/mobilemoney"

    ENDPOINTS: Dict[str, str] = {
        "payment": "/v1",
        "status": "/v1/getStatus/{transaction_id}",
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
        """ Validate the credentials for Bizao. """
        
        return all([
            self.config.api_key, 
            self.config.extra,                              # Extra configs must be set
            # DEVELOPMENT CREDENTIALS
            self.config.extra.get("dev_client_id"),         # Bizao uses CLIENT_ID 
            self.config.extra.get("dev_client_secret"),     # and secret key (token)
            self.config.extra.get("dev_token_url"),         # Token Url
            # PRODUCTION CREDENTIALS
            self.config.extra.get("prod_client_id"),         
            self.config.extra.get("prod_client_secret"),     
            self.config.extra.get("prod_token_url"),         
            # EXTRA
            self.config.extra.get("country-code"),
            self.config.extra.get("mno-name"),              # The provider to use in Bizao's name
            self.config.extra.get("channel"),               # Payment channel, choices are 'web', 'tpe', 'Ussd'
            self.config.extra.get("lang"),
            self.config.extra.get("cancel_url")
        ])
    
    def get_credentials(self):
        """Get the credentials for Bizao."""
        # NOTE that credentials are checked in the constructor

        return {
            "client_id": (
                self.config.extra.get('dev_client_id','') if
                self.config.environment == 'sandbox' else
                self.config.extra.get('prod_client_id','')
            ),
            "client_secret": (
                self.config.extra.get('dev_client_secret','') if
                self.config.environment == 'sandbox' else
                self.config.extra.get('prod_client_secret','')
            )
        }
    
    def get_extra_headers(self,**extra):
        """Returns extra headers"""
        
        return {
            'country-code': self.config.extra.get('country-code').lower(), 
            'mno-name': self.config.extra.get('mno-name').lower(),
            'channel': self.config.extra.get('channel'),
            'lang': self.config.extra.get('lang','FR').lower()
        } # if extra.get('transaction',None) else {}
    
    def get_headers(
        self, 
        c_type = 'application/json',
        authorization = False,
        extra = False, **kwargs
    ):
        """Get the headers for Bizao."""

        headers = {
            'Content-Type': c_type
        }

        if authorization:
            headers |= self.get_authrizations(authorization)

        # ADD EXTRA HEADERS
        if extra:
            headers |= self.get_extra_headers(**kwargs)
       
        return headers
    
    def get_authrizations(self,auth = False, basic = False) -> dict:
        ''' Returns authrization informations. '''
        return {
            'Authorization': f'Bearer {self.config.api_key}',
        }   if auth else {}
    
    def get_token_url(self) -> str:
        """Return a token url based on environment."""

        return (
            self.config.extra.get("dev_token_url",'') if
            self.config.environment == 'sandbox' else
            self.config.extra.get("prod_token_url",'')
        )
    
    async def authenticate(self):
        """Make auth request and get auth token."""

        # First get client identifiers from config
        creds = self.get_credentials()
        
        # Second, generate a basic token from creds
        basic_token = base64.b64encode(
            bytes(
                f"{creds['client_id']}:{creds['client_secret']}",
                'utf-8'
            )
        )
        # Now, build headers
        headers = self.get_headers(
            c_type = 'application/x-www-form-urlencoded',   # CONTENT TYPE
        )
        # Update it with Authorization header
        headers |= {'Authorization': f'Basic {str(basic_token,"utf-8")}'}

        # Make request to get the access_token
        async with HTTPClient(
            self.get_token_url(),
            default_headers = headers
        ) as client:
            response = await client.post(
                '',
                params = {'grant_type': 'client_credentials'},
            )

            # Then Check for success
            if response.status in range(200,300):
                self.config.api_key = response.data.get('access_token')
                return

            # Raise AuthenticationError
            raise AuthenticationError(
                message = (
                    f"Authentication failed with status {response.status}.\n"
                    f"url: {response.url}"
                ),
                code = str(response.status),
                details = response.data
            )
        
    def _initialize_adapter(self):
        """Override Initialize Adapter method to add authentications."""
        asyncio.run(self.authenticate())
        return super()._initialize_adapter()

    def format_transaction(
        self, 
        transaction: TransactionDetail
    ) -> Dict[str, Any]:
        """Format the transaction data into a Bizao's expected format."""

        # Check if the transaction is valid
        self.validate_transaction(transaction)     # Will raise ValidationError if needed.

        # Then build payload
        payload = {
            "currency": transaction.currency,
            "order_id": transaction.transaction_id,
            "amount": int(transaction.amount),
            "reference": transaction.reference,
            "state": dict_to_encoded_query_string(transaction.metadata),
            "return_url": transaction.return_url or self.config.return_url,
            "cancel_url": self.config.extra.get("cancel_url",''),
            "NotifUrl": transaction.callback_url or self.config.callback_url
        }
        # Optional for web channel but required for TPE and USSD channels 
        if self.config.extra.get("channel") == "tpe":
            payload["user_msisdn"] = transaction.customer.phone_number.replace(" ", "")

        return payload
    
    def get_normalize_status(self, status):
        """ Normalize the status of a transaction. """

        # Mapp Bizao statues to EasySwitch standardized status
        # Bizao's documentation is not very clear about available Transaction status
        # so we'll move on with followings.
        statues = {
            # Successful status
            'SUCCESSFUL': TransactionStatus.SUCCESSFUL,
            'OK': TransactionStatus.SUCCESSFUL,
            # Pending status
            'PENDING': TransactionStatus.PENDING,
            'WAITING': TransactionStatus.PENDING,
            # Failure status
            'FAILURE': TransactionStatus.FAILED,
            'FAILED': TransactionStatus.FAILED,
            'FAIL': TransactionStatus.FAILED,
            # Cancelation status
            'CANCELLED': TransactionStatus.CANCELLED,
            # Error status
            'ERROR': TransactionStatus.ERROR,
            # Expiry status
            'EXPIRED': TransactionStatus.EXPIRED
        }

        return statues.get(status, TransactionStatus.UNKNOWN)
    
    def validate_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> bool:
        """Validate the authenticity of a Bizao webhook."""
        # Bizao signs webhooks with an HMAC-SHA256 of the raw body,
        # sent in the X-Hub-Signature header.
        signature = headers.get("X-Hub-Signature") or headers.get("x-hub-signature")
        secret = self.config.extra.get("secret") or self.config.api_secret
        if not signature or not secret:
            return False

        # Recompute the expected signature from the JSON body
        raw_body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        expected = hmac.new(secret.encode("utf-8"), msg=raw_body, digestmod=hashlib.sha256).hexdigest()
        # Bizao sometimes prefixes the signature with "sha256="
        received = signature.replace("sha256=", "").strip()
        return hmac.compare_digest(expected, received)
    
    def parse_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> WebhookEvent:
        """Parse a validated Bizao webhook into a standard WebhookEvent."""
        if not self.validate_webhook(payload, headers):
            raise AuthenticationError(
                message="Invalid webhook signature",
                provider=self.provider_name()
            )

        return WebhookEvent(
            event_type=payload.get("event", payload.get("status", "unknown")),
            provider=self.provider_name(),
            transaction_id=str(payload.get("order_id", payload.get("transaction_id", ""))),
            status=self.get_normalize_status(payload.get("status", "").upper()),
            amount=float(payload.get("amount", 0)),
            currency=payload.get("currency", "XOF"),
            created_at=payload.get("created_at"),
            raw_data=payload,
            metadata=payload.get("metadata", {}),
        )
    
    async def send_payment(self, transaction: TransactionDetail) -> PaymentResponse:
        """
        Send a payment request to Bizao.
        """
        # First we need to format the transaction
        order = self.format_transaction(transaction)

        # Then send the request to provider
        async with self.get_client() as client:

            response = await client.post(
                endpoint = self.ENDPOINTS["payment"],
                json_data = order,
                headers = self.get_headers(
                    authorization = True,
                    extra = True
                ),
            )

            # Check for success
            if response.status in range(200,300):
                # Then Process data and return Payment Response.
                status_atr = (
                    'message' if 
                    self.config.extra.get('channel','web') == 'web' 
                    else 'status'
                )
                data = response.data
                return PaymentResponse(
                    transaction_id = transaction.transaction_id,
                    reference = transaction.reference,
                    provider = self.provider_name(),
                    status = self.get_normalize_status(data.get(status_atr,'').upper()),
                    currency = transaction.currency,
                    amount = data.get('amount') or transaction.amount,      # In case of web channel.
                    payment_link = data.get('payment_url',''),
                    transaction_token = data.get('pay_token',''),           # Will be empty in case of tpe and ussd channels
                    metadata = encoded_query_string_to_dict(data.get('state','')),
                    raw_response = data
                )

            # If the response is not successful, raise an API error
            raise PaymentError(
                message = (
                    f"Payment request failed with status {response.status}.\n"
                    f"url: {response.url}\n {response.data}"
                ),
                status_code = response.status,
                raw_response = response.data
            )
        
    async def check_status(self, transaction_id: str) -> TransactionStatusResponse:
        """
        Check the status of a transaction.
        """

        # Initialize http client
        async with self.get_client() as client:
            # Then make the request
            response = await client.get(
                endpoint=self.ENDPOINTS["status"].format(
                    transaction_id = transaction_id
                ),
                headers = self.get_headers(
                    authorization = True,
                    extra = True
                ),
            )

            data = response.data

            # Return Transaction status Response
            return TransactionStatusResponse(
                transaction_id = transaction_id,
                provider = self.provider_name(),
                status = self.get_normalize_status(data.get('status','').upper()),
                amount = data.get("amount"),
                data = data
            )
        
    async def cancel_transaction(self, transaction_id):
        """
        Cancel a transaction.
        """
        # Bizao does not support transaction cancellation
        raise UnsupportedOperationError(
            message="Bizao does not support transaction cancellation",
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
        # Bizao does not support refunds
        raise UnsupportedOperationError(
            message="Bizao does not support refunds",
            provider = self.provider_name()
        )
    
    async def get_transaction_detail(self, transaction_id: str) -> TransactionDetail:
        """
        Get the details of a transaction.
        """
        # Bizao does not support 
        raise UnsupportedOperationError(
            message = (
                "Bizao does not allow to retrive transactions by id. "
                "Use check_status instead."
            ),
            provider = self.provider_name()
        )
