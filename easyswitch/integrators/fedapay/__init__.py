"""
EasySwitch - Fedapay Integrator
"""
import hashlib
import hmac
import json
from typing import Any, ClassVar, Dict, List, Optional
from dateutil import parser

from easyswitch.adapters.base import AdaptersRegistry, BaseAdapter
from easyswitch.exceptions import (
    AuthenticationError, BalanceError, CurrencyError, 
    CustomerError, LogError, PaymentError,
    UnsupportedOperationError, WebhookError, WebhookValidationError,
)
from easyswitch.integrators.fedapay.types import (
    BalanceDetail, CurrencyResponse, CustomerSearchResponse, 
    FedapayCustomerUpdate, FedapayTransactionUpdate, LogDetail, 
    LogsResponse, PaymentLinkResponse, TransactionSearchResponse, 
    WebhookDetail, WebhooksResponse
)
from easyswitch.integrators.fedapay.utils import FedapayCurrencyMapper
from easyswitch.types import (
    Currency, CustomerInfo, PaginationMeta, PaymentResponse,
    Provider, TransactionDetail, TransactionStatus,
    TransactionStatusResponse, TransactionType, WebhookEvent,
)
from easyswitch.utils import parse_phone


####
##      FEDAPAY INTEGRATOR
#####
@AdaptersRegistry.register()
class FedapayAdapter(BaseAdapter):
    """FedaPay Integrator for EasySwitch SDK."""
    
    def __str__(self):
        return "FedaPay Adapter"

    SANDBOX_URL: str = "https://sandbox-api.fedapay.com"

    PRODUCTION_URL: str = "https://api.fedapay.com"

    ENDPOINTS: Dict[str, str] = {
        # Customer
        "create_customer": "/v1/customers",
        "get_customer": "/v1/customers/{id}",
        "update_customer": "/v1/customers/{id}",
        "delete_customer": "/v1/customers/{id}",
        "search_customers": "/v1/customers/search",
        
        # Transactions
        "create_transaction": "/v1/transactions",
        "get_transaction": "/v1/transactions/{id}",
        "update_transaction": "/v1/transactions/{id}",
        "delete_transaction": "/v1/transactions/{id}",
        "search_transactions": "/v1/transactions/search",
        "get_payment_link_for_transaction": "/v1/transactions/{id}/token",
        
        # Balances
        "get_balance": "/v1/balances/{id}",
        "get_all_balances": "/v1/balances",
        
        # Currencies
        "get_currency": "/v1/currencies/{id}",
        "get_all_currencies": "/v1/currencies",
        
        # Logs
        "get_all_logs": "/v1/logs",
        
        # Webhooks
        "get_webhook": "/v1/webhooks/{id}",
        "get_all_webhooks": "/v1/webhooks",
    }

    SUPPORTED_CURRENCIES: ClassVar[List[Currency]] = [
        Currency.XOF,
    ]

    MIN_AMOUNT: ClassVar[Dict[Currency, float]] = {
        Currency.XOF: 1.0,
    }

    MAX_AMOUNT: ClassVar[Dict[Currency, float]] = {
        Currency.XOF: 999999998.0,
    }

    def validate_credentials(self) -> bool:
        """ Validate the credentials for FedaPay. """
        
        return all([
            self.config.api_secret,
        ])
    
    def get_credentials(self):
        """Get the credentials for FedaPay."""
        # NOTE that credentials are checked in the constructor

        return {
            "secret_key": self.config.api_secret,
        }
    
    def get_headers(self, authorization: bool=False):
        """Get the headers for FedaPay API requests."""

        headers = {
            "Content-Type":"application/json"
        }
        # Add Authorizations if needed
        if authorization:
            headers["Authorization"] = f"Bearer {self.config.api_secret}"

        return headers
    
    ############################
    ##### Customer Methods  ####
    ############################
    def validate_customer(self, customer: CustomerInfo):
        """
        Validate the customer data before sending it to FedaPay's API.
        This method checks if all required fields are present and correctly formatted.
        Args:
            customer (CustomerInfo): The customer details to be validated.
        Raises:
            ValidationError: If the customer data is invalid.
        """
        
        if customer.email:
            return
        
        if not customer.phone_number:
            raise CustomerError(
                message="Customer phone number is required if email is not provided",
                provider=self.provider_name()
            )
        
        parsed_phone_number = parse_phone(customer.phone_number, raise_exception=True)
        
        if not parsed_phone_number.get("country_code") or not parsed_phone_number.get("country_alpha2"):
            raise CustomerError(
                message="Phone number must include country alpha2 and national number",
                provider=self.provider_name()
            )
    
    def format_customer(self, customer: CustomerInfo) -> Dict[str, Any]:
        """
        Format the customer data into a standardized format.
        This method prepares the customer data to be sent to FedaPay's API.
        Args:
            customer (CustomerInfo): The customer details to be formatted.
        Returns:
            Dict[str, Any]: The formatted customer data.
        Raises:
            ValidationError: If the customer data is invalid.
        """
        
        # Check if the customer is valid
        self.validate_customer(customer)
        
        # Parse the phone number using the utility function
        parsed_phone_number = parse_phone(
            customer.phone_number,
            raise_exception=True
        )
        return {
            "email": customer.email or "",
            "firstname": customer.first_name or "",
            "lastname": customer.last_name or "",
            "phone_number": {
                "number": parsed_phone_number.get("national_number"),   # Will return the phone number
                "country": parsed_phone_number.get("country_alpha2")  # Will return the country code,
            },
        }
    
    def _build_customer_detail(
        self,
        data: Dict[str, Any],
    ) -> CustomerInfo:
        """ Build a CustomerInfo object from the FedaPay API response data.
        Args:
            data (Dict[str, Any]): The raw data from the FedaPay API response.
            raw_response (Optional[Dict[str, Any]]): The full raw response data.
        Returns:
            CustomerInfo: The customer details.
        Raises:
            CustomerError: If the customer data is invalid or if the ID is missing.
        """
        
        return CustomerInfo(
            id=data.get("id"),
            email=data.get("email"),
            first_name=data.get("firstname"),
            last_name=data.get("lastname"),
            metadata={k: v for k, v in data.items() if k not in {
                "id", "email", "firstname", "lastname"
            }},
        )
    
    async def create_customer(self, customer: CustomerInfo) -> CustomerInfo:
        """
        Create a new customer in FedaPay's system.
        This method sends the customer data to FedaPay's API and returns the created customer information.
        Args:
            customer (CustomerInfo): The customer details to be created.
        Returns:
            CustomerInfo: The created customer information.
        Raises:
            CustomerError: If the customer creation fails or if the data is invalid.
        """
        
        customer = self.format_customer(customer)
        
        async with self.get_client() as client:
            response = await client.post(
                endpoint=self.ENDPOINTS["create_customer"],
                json_data=customer,
                headers=self.get_headers(authorization=True)
            )
                                    
            if response.status in range(200, 300):
                customer_data: Dict[str, Any] = response.data.get("v1/customer", {})
                
                return self._build_customer_detail(customer_data)
        
            # If the response is not successful, raise a CustomerError
            raise CustomerError(
                message="Failed to create customer",
                status_code=response.status,
                raw_response=response.data
            )
    
    async def update_customer(self, customer_id: int, customer: FedapayCustomerUpdate) -> CustomerInfo:
        """
        Update an existing customer in FedaPay's system.
        This method sends the updated customer data to FedaPay's API and returns the updated customer information.
        Args:
            customer_id (int): The ID of the customer to be updated.
            customer (FedapayCustomerUpdate): The updated customer details.
        Returns:
            CustomerInfo: The updated customer information.
        Raises:
            CustomerError: If the customer update fails or if the data is invalid.
        """
                
        async with self.get_client() as client:
            response = await client.put(
                endpoint=self.ENDPOINTS["update_customer"].format(id=customer_id),
                json_data=customer.to_payload(),
                headers=self.get_headers(authorization=True)
            )
            
            if response.status in range(200, 300):
                customer_data: Dict[str, Any] = response.data.get("v1/customer", {})
                
                return self._build_customer_detail(customer_data)
        
            # If the response is not successful, raise a CustomerError
            raise CustomerError(
                message=f"Failed to update customer with ID {customer_id}",
                status_code=response.status,
                raw_response=response.data
            )
        
    async def delete_customer(self, customer_id: int) -> bool:
        """
        Delete a customer from FedaPay's system.
        This method sends a request to FedaPay's API to delete the specified customer.
        Args:
            customer_id (int): The ID of the customer to be deleted.
        Returns:
            bool: True if the customer was successfully deleted, False otherwise.
        Raises:
            CustomerError: If the customer deletion fails or if the ID is invalid.
        """
        
        async with self.get_client() as client:
            response = await client.delete(
                endpoint=self.ENDPOINTS["delete_customer"].format(id=customer_id),
                headers=self.get_headers(authorization=True)
            )
            
            if response.status in range(200, 300):
                return True
        
            # If the response is not successful, raise a CustomerError
            raise CustomerError(
                message=f"Failed to delete customer with ID {customer_id}",
                status_code=response.status,
                raw_response=response.data
            )
    
    async def search_customers(self) -> CustomerSearchResponse:
        """
        Search for customers in FedaPay's system.
        This method retrieves a list of customers and their metadata from FedaPay's API.
        Returns:
            CustomerSearchResponse: The response containing a list of customers and pagination metadata.
        Raises:
            CustomerError: If the customer search fails or if there is an error in the request.
        """
        async with self.get_client() as client:
            response = await client.get(
                endpoint=self.ENDPOINTS["search_customers"],
                headers=self.get_headers(authorization=True)
            )
            
            if response.status in range(200, 300):
                customers_data: List[Dict[str, Any]] = response.data.get("v1/customers", [])
                meta_data: Dict[str, Any] = response.data.get("meta", {})
                customers = [
                    CustomerInfo(
                        id=customer.get("id"),
                        email=customer.get("email"),
                        first_name=customer.get("firstname"),
                        last_name=customer.get("lastname"),
                        metadata={
                            "phone_number_id": customer.get("phone_number_id"),
                            "account_id": customer.get("account_id"),
                            "full_name": customer.get("full_name"),
                            "created_at": customer.get("created_at"),
                            "updated_at": customer.get("updated_at"),
                            "deleted_at": customer.get("deleted_at"),
                            "klass": customer.get("klass"),
                        }
                    ) for customer in customers_data
                ]
                meta = PaginationMeta(
                    current_page=meta_data.get("current_page"),
                    next_page=meta_data.get("next_page"),
                    prev_page=meta_data.get("prev_page"),
                    per_page=meta_data.get("per_page"),
                    total_pages=meta_data.get("total_pages"),
                    total_count=meta_data.get("total_count"),
                )
                return CustomerSearchResponse(customers=customers, meta=meta)

        
            # If the response is not successful, raise a CustomerError
            raise CustomerError(
                message="Failed to search customers",
                status_code=response.status,
                raw_response=response.data
            )
    
    async def get_customer_detail(self, customer_id: int) -> Optional[CustomerInfo]:
        """
        Retrieve the details of a customer by their ID.
        Args:
            customer_id (int): The ID of the customer to retrieve.
        Returns:
            CustomerInfo: The details of the customer.
        Raises:
            CustomerError: If the customer cannot be found or if there is an error in the request.
        """
        async with self.get_client() as client:
            response = await client.get(
                endpoint=self.ENDPOINTS["get_customer"].format(id=customer_id),
                headers=self.get_headers(authorization=True)
            )
                        
            if response.status in range(200, 300):
                customer_data: Dict[str, Any] = response.data.get("v1/customer", {})
                
                return self._build_customer_detail(customer_data)
                
            raise CustomerError(
                message=f"Failed to fetch customer for ID {customer_id}",
                status_code=response.status,
                raw_response=response.data
            )
    
    ##############################
    ##### Transaction Methods ####
    ##############################
    def format_transaction(self, transaction: TransactionDetail) -> Dict[str, Any]:
        """
        Format the transaction data into a standardized format.
        This method prepares the transaction data to be sent to FedaPay's API.
        It includes parsing the phone number and ensuring all required fields are present.
        Args:
            transaction (TransactionDetail): The transaction details to be formatted.
            Returns:
                Dict[str, Any]: The formatted transaction data.
        Raises:
            ValidationError: If the transaction data is invalid.
        """

        # Check if the transaction is valid
        self.validate_transaction(transaction)     # Will raise ValidationError if needed.

        # Parse the phone number using the utility function
        parsed_phone = parse_phone(
            transaction.customer.phone_number,
            raise_exception=True
        )
        
        return {
            "amount": int(transaction.amount),
            "currency": {'iso': transaction.currency},
            "description": transaction.reason,
            "callback_url": transaction.callback_url or self.config.callback_url,
            "custom_metadata": transaction.metadata,
            "customer": {
                "id": transaction.customer.id,
                "email": transaction.customer.email,
                "firstname": transaction.customer.first_name,
                "lastname": transaction.customer.last_name,
                "phone_number": {
                    "number": parsed_phone.get("national_number"),    # Will return the phone number
                    "country": parsed_phone.get("country_alpha2")  # Will return the country code,
                },
            },
        }

    async def send_payment(self, transaction: TransactionDetail) -> PaymentResponse:
        """
        Send a payment request to FedaPay.
        Args:
            transaction (TransactionDetail): The transaction details to be processed.
        Returns:
            PaymentResponse: The response containing payment details.
        Raises:
            PaymentError: If the payment request fails.
        """
        order = self.format_transaction(transaction)

        async with self.get_client() as client:
            # Send payment request
            response = await client.post(
                endpoint=self.ENDPOINTS["create_transaction"],
                json_data=order,
                headers=self.get_headers(authorization=True)
            )
                        
            if response.status in range(200, 300):
                transaction_data: Dict[str, Any] = response.data.get("v1/transaction", {})
                currency_iso = FedapayCurrencyMapper.get_iso(int(transaction_data.get("currency_id")))
                customer = CustomerInfo(
                    id=transaction_data.get("customer_id"),
                    email=transaction.customer.email,
                    first_name=transaction.customer.first_name,
                    last_name=transaction.customer.last_name,
                    phone_number=transaction.customer.phone_number,
                    metadata=transaction.customer.metadata,
                )
                
                return PaymentResponse(
                    transaction_id=transaction_data.get("id"),
                    provider=self.provider_name(),
                    status=TransactionStatus.PENDING,
                    amount=transaction_data.get("amount"),
                    currency=Currency(currency_iso),
                    reference=transaction_data.get("reference"),
                    payment_link=transaction_data.get("payment_url"),
                    customer=customer,
                    created_at=parser.parse(transaction_data.get("created_at")),
                    raw_response=response.data,
                    metadata=transaction_data.get("metadata", {})
                )

            raise PaymentError(
                message="Payment request to FedaPay failed",
                status_code=response.status,
                raw_response=response.data
            )
    
    def get_normalize_status(self, status):
        """ Normalize the status of a transaction. """

        # FedaPay uses the following statuses
        statues = {
            "approved": TransactionStatus.SUCCESSFUL,
            # The payment was successfully completed by the customer.
            # The transaction is marked as approved.

            "pending": TransactionStatus.PENDING,
            # The transaction was created and is waiting for payment.
            # This is the default status when a transaction is first created.

            "declined": TransactionStatus.FAILED,
            # The payment failed.
            # This usually means the customer had insufficient funds or an issue with their account.

            "expired": TransactionStatus.EXPIRED,
            # The transaction expired because the customer did not complete the payment in time.

            "canceled": TransactionStatus.CANCELLED,
            # The transaction was canceled by the customer,
            # either deliberately or accidentally, before payment was completed.

            "refunded": TransactionStatus.REFUNDED,
            # The payment was successfully refunded to the customer.

            "transferred": TransactionStatus.TRANSFERRED,
            # The transaction amount has been transferred to the merchant's account balance.
            # Only approved transactions are eligible for transfer.
        }
        
        return statues.get(status, TransactionStatus.UNKNOWN)
    
    async def _build_transaction_detail(
        self, 
        data: Dict[str, Any], 
        raw_response: Optional[Dict[str, Any]] = None,
        fetch_customer: bool = True
    ) -> TransactionDetail:
        """
        Build a TransactionDetail object from the FedaPay API response data.
        Args:
            data (Dict[str, Any]): The raw data from the FedaPay API response.
            raw_response (Optional[Dict[str, Any]]): The full raw response data.
            fetch_customer (bool): Whether to fetch customer details or not.
        Returns:
            TransactionDetail: The transaction details.
        Raises:
            PaymentError: If the customer ID is missing in the transaction data.
        """
        
        customer_id = data.get("customer_id")
        if not customer_id:
            raise PaymentError(
                message="Customer ID is missing in transaction data",
                raw_response=raw_response
            )
            
        customer = None
        # Fetch customer details if required
        if fetch_customer:
            customer = await self.get_customer_detail(customer_id)
        else:
            customer = CustomerInfo(id=customer_id)
        
        normalized_status = self.get_normalize_status(data.get("status"))
        
        return TransactionDetail(
            transaction_id=data.get("id"),
            provider=Provider.FEDAPAY,
            amount=data.get("amount"),
            currency=FedapayCurrencyMapper.get_iso(data.get("currency_id")),
            status=normalized_status,
            transaction_type=TransactionType.PAYMENT,
            created_at=parser.parse(data.get("created_at")) if data.get("created_at") else None,
            updated_at=parser.parse(data.get("updated_at")) if data.get("updated_at") else None,
            completed_at=parser.parse(data.get("approved_at")) if data.get("approved_at") else None,
            customer=customer,
            reference=data.get("reference"),
            reason=data.get("description"),
            callback_url=data.get("callback_url"),
            metadata={k: v for k, v in data.items() if k not in {
                "id", 
                "amount", 
                "currency", 
                "status", 
                "created_at", 
                "updated_at",
                "approved_at",
                "customer_id", 
                "reference", 
                "reason",
                "callback_url",
            }},
            raw_data=raw_response if raw_response is not None else data
        )

    async def get_transaction_detail(self, transaction_id: str) -> TransactionDetail:
        """
        Retrieve the details of a transaction by its ID.
        Args:
            transaction_id (str): The ID of the transaction to retrieve.
        Returns:
            TransactionDetail: The details of the transaction.
        Raises:
            PaymentError: If the transaction cannot be found or if there is an error in the request.
        """
        async with self.get_client() as client:
            response = await client.get(
                endpoint=self.ENDPOINTS["get_transaction"].format(id=transaction_id),
                headers=self.get_headers(authorization=True)
            )

            if response.status in range(200, 300):
                data: Dict[str, Any] = response.data.get("v1/transaction", {})
                
                return await self._build_transaction_detail(data, response.data, fetch_customer=True)
                
            raise PaymentError(
                message="Failed to fetch transaction detail", 
                status_code=response.status, 
                raw_response=response.data
            )

    def format_transaction_for_update(self, transaction: FedapayTransactionUpdate) -> Dict[str, Any]:
        """
        Format the transaction data into a standardized format.
        This method prepares the transaction data to be sent to FedaPay's API.
        It includes parsing the phone number and ensuring all required fields are present.
        Args:
            transaction (FedapayTransactionUpdate): The transaction details to be formatted.
        Returns:
            Dict[str, Any]: The formatted transaction data.
        """
        data = {}
        
        if transaction.amount is not None:
            data["amount"] = int(transaction.amount)
        if transaction.status is not None:
            data["status"] = transaction.status
        if transaction.description is not None:
            data["description"] = transaction.description
        if transaction.callback_url is not None:
            data["callback_url"] = transaction.callback_url
        
        return data
    
    async def update_transaction(self, transaction_id: str, transaction: FedapayTransactionUpdate) -> TransactionDetail:
        """
        Update an existing transaction in FedaPay's system.
        This method sends the updated transaction data to FedaPay's API and returns the updated transaction information.
        Args:
            transaction_id (str): The ID of the transaction to be updated.
            transaction (FedapayTransactionUpdate): The updated transaction details.
        Returns:
            TransactionDetail: The updated transaction information.
        Raises:
            PaymentError: If the transaction update fails or if the data is invalid.
        """
        
        # Format the transaction data
        formatted_transaction = self.format_transaction_for_update(transaction)
        
        async with self.get_client() as client:
            response = await client.put(
                endpoint=self.ENDPOINTS["update_transaction"].format(id=transaction_id),
                json_data=formatted_transaction,
                headers=self.get_headers(authorization=True)
            )
            
            if response.status in range(200, 300):
                data: Dict[str, Any] = response.data.get("v1/transaction", {})
                
                return await self._build_transaction_detail(data, response.data, fetch_customer=True)
        
            # If the response is not successful, raise a PaymentError
            raise PaymentError(
                message=f"Failed to update transaction with ID {transaction_id}",
                status_code=response.status,
                raw_response=response.data
            )
    
    async def delete_transaction(self, transaction_id: int) -> bool:
        """
        Delete a transaction from FedaPay's system.
        This method sends a request to FedaPay's API to delete the specified transaction.
        Args:
            transaction_id (int): The ID of the transaction to be deleted.
        Returns:
            bool: True if the transaction was successfully deleted, False otherwise.
        Raises:
            PaymentError: If the transaction deletion fails or if the ID is invalid.
        """
        
        async with self.get_client() as client:
            response = await client.delete(
                endpoint=self.ENDPOINTS["delete_transaction"].format(id=transaction_id),
                headers=self.get_headers(authorization=True)
            )
            
            if response.status in range(200, 300):
                return True
        
            # If the response is not successful, raise a PaymentError
            raise PaymentError(
                message=f"Failed to delete transaction with ID {transaction_id}",
                status_code=response.status,
                raw_response=response.data
            )
    
    async def search_transactions(self) -> TransactionSearchResponse:
        """
        Search for transactions in FedaPay's system.
        This method retrieves a list of transactions and their metadata from FedaPay's API.
        Returns:
            TransactionSearchResponse: The response containing a list of transactions and pagination metadata.
        Raises:
            PaymentError: If the transaction search fails or if there is an error in the request.
        """
        
        async with self.get_client() as client:
            response = await client.get(
                endpoint=self.ENDPOINTS["search_transactions"],
                headers=self.get_headers(authorization=True)
            )
            
            if response.status in range(200, 300):
                transactions_data: List[Dict[str, Any]] = response.data.get("v1/transactions", [])
                meta_data: Dict[str, Any] = response.data.get("meta", {})
                transactions = [
                    await self._build_transaction_detail(data=transaction, fetch_customer=False)
                    for transaction in transactions_data
                ]
                meta = PaginationMeta(
                    current_page=meta_data.get("current_page"),
                    next_page=meta_data.get("next_page"),
                    prev_page=meta_data.get("prev_page"),
                    per_page=meta_data.get("per_page"),
                    total_pages=meta_data.get("total_pages"),
                    total_count=meta_data.get("total_count"),
                )
                return TransactionSearchResponse(transactions=transactions, meta=meta)
        
            # If the response is not successful, raise a PaymentError
            raise PaymentError(
                message="Failed to search transactions",
                status_code=response.status,
                raw_response=response.data
            )
    
    async def get_payment_link_for_transaction(self, transaction_id: str) -> PaymentLinkResponse:
        """
        Get the payment link for a transaction.
        This method retrieves the payment link for a specific transaction ID from FedaPay's API.
        Args:
            transaction_id (str): The ID of the transaction to retrieve the payment link for.
        Returns:
            str: The payment link for the transaction.
        Raises:
            PaymentError: If the transaction cannot be found or if there is an error in the request.
        """
        
        async with self.get_client() as client:
            response = await client.post(
                endpoint=self.ENDPOINTS["get_payment_link_for_transaction"].format(id=transaction_id),
                headers=self.get_headers(authorization=True)
            )
                        
            if response.status in range(200, 300):
                data: Dict[str, Any] = response.data or {}
                payment_link = data.get("url")
                if not payment_link:
                    raise PaymentError(
                        message=f"No payment link found for transaction {transaction_id}",
                        status_code=response.status,
                        raw_response=response.data
                    )
                return PaymentLinkResponse(
                    token=data.get("token"),
                    url=payment_link,
                    raw_response=response.data
                )
        
            raise PaymentError(
                message=f"Failed to get payment link for transaction {transaction_id}",
                status_code=response.status,
                raw_response=response.data
            )
       
    async def refund(
        self, 
        transaction_id: str, 
        amount: Optional[float] = None
        , 
        reason: Optional[str] = None
    ) -> PaymentResponse:
        """
        Refund a transaction.
        """
        # FedaPay does not support refunds
        raise UnsupportedOperationError(
            message = "FedaPay does not support refunds from API",
            provider = self.provider_name(),
        )
    
    async def check_status(self, transaction_id: str) -> TransactionStatusResponse:
        """
        Check the status of a transaction using FedaPay's API.
        Args:
            transaction_id (str): The ID of the transaction to check.
        Returns:
            TransactionStatusResponse: The status of the transaction.
        Raises:
            PaymentError: If the transaction cannot be found or if there is an error in the request.
        """
        async with self.get_client() as client:
            response = await client.get(
                endpoint=self.ENDPOINTS["get_transaction"].format(id=transaction_id),
                headers=self.get_headers(authorization=True)
            )

            if response.status in range(200, 300):
                transaction_data: Dict[str, Any] = response.data.get("v1/transaction", {})
                status = self.get_normalize_status(transaction_data.get("status"))

                return TransactionStatusResponse(
                    transaction_id=transaction_id,
                    provider=self.provider_name(),
                    status=status,
                    amount = transaction_data.get("amount"),
                    data=transaction_data
                )

            raise PaymentError(
                message=f"Failed to check status for transaction {transaction_id}",
                status_code=response.status,
                raw_response=response.data
            )
            
    async def cancel_transaction(self, transaction_id):
        """
        Cancel a transaction.
        """
        # FedaPay does not support transaction cancellation
        raise UnsupportedOperationError(
            message = "FedaPay does not support transaction cancellation",
            provider = self.provider_name(),
        )
    
    ############################
    ##### Balance Methods   ####
    ############################
    def _build_balance_detail(
        self, 
        data: Dict[str, Any], 
    ) -> BalanceDetail:
        """
        Build a BalanceDetail object from the FedaPay API response data.
        Args:
            data (Dict[str, Any]): The API response data.
        Returns:
            BalanceDetail: The balance details.
        Raises:
            ValueError: If the response data is invalid or incomplete.
        """
        return BalanceDetail(
            id=int(data.get("id")),
            amount=float(data.get("amount")),
            mode=data.get("mode"),
            provider=self.provider_name(),
            created_at=parser.parse(data.get("created_at")),
            updated_at=parser.parse(data.get("updated_at")),
            metadata={k: v for k, v in data.items() if k not in {
                "id", "amount", "mode", "provider", "created_at", "updated_at"
            }},
        )

    async def get_all_balances(self) -> List[BalanceDetail]:
        """
        Retrieve all balances for the account using FedaPay's API.
        Returns:
            List[BalanceDetail]: A list of BalanceDetail objects containing balance details.
        Raises:
            BalanceError: If the balance retrieval fails or if there is an error in the request.
        """
        
        async with self.get_client() as client:
            response = await client.get(
                endpoint=self.ENDPOINTS["get_all_balances"],
                headers=self.get_headers(authorization=True)
            )
            
            if response.status in range(200, 300):
                balances_data: List[Dict[str, Any]] = response.data.get("v1/balances", [])
                
                balances = [
                    self._build_balance_detail(balance)
                    for balance in balances_data
                ]
                
                return balances
        
            raise BalanceError(
                message="Failed to fetch all balances",
                status_code=response.status,
                raw_response=response.data
            )

    async def get_balance_detail(self, balance_id: int) -> BalanceDetail:
        """
        Retrieve the balance for a specific account ID using FedaPay's API.
        Args:
            balance_id (int): The ID of the account to retrieve the balance for.
        Returns:
            BalanceDetail: An object containing the balance details.
        Raises:
            BalanceError: If the balance cannot be found or if there is an error in the request.
        """
        
        async with self.get_client() as client:
            response = await client.get(
                endpoint=self.ENDPOINTS["get_balance"].format(id=balance_id),
                headers=self.get_headers(authorization=True)
            )
            
            if response.status in range(200, 300):
                balance_data: Dict[str, Any] = response.data.get("v1/balance", {})
                
                return self._build_balance_detail(balance_data)
        
            raise BalanceError(
                message=f"Failed to fetch balance for ID {id}",
                status_code=response.status,
                raw_response=response.data
            )

    ############################
    ##### Currency Methods #####
    ############################
    async def get_currency_detail(self, currency_id: int) -> CurrencyResponse:
        """
        Retrieve currency details by currency ID using FedaPay's API.
        This method fetches currency information such as name, ISO code, and modes.
        Args:
            currency_id (int): The ID of the currency to retrieve.
        Returns:
            CurrencyResponse: An object containing the currency's details.
        Raises:
            CurrencyError: If the currency cannot be found or if there is an error in the request.
        """
        
        async with self.get_client() as client:
            response = await client.get(
                endpoint=self.ENDPOINTS["get_currency"].format(id = currency_id),
                headers=self.get_headers(authorization=True)
            )
            
            if response.status in range(200, 300):
                currency_data: Dict[str, Any] = response.data.get("v1/currency", {})

                return CurrencyResponse(
                    currency_id=currency_data.get("id"),
                    name=currency_data.get("name"),
                    provider=self.provider_name(),
                    iso=currency_data.get("iso"),
                    created_at=parser.parse(currency_data.get("created_at")),
                    updated_at=parser.parse(currency_data.get("updated_at")),
                    modes=currency_data.get("modes", []),
                    raw_response=response.data,
                )
        
            raise CurrencyError(
                message=f"Failed to fetch currency for ID {id}",
                status_code=response.status,
                raw_response=response.data
            )
    
    async def get_all_currencies(self) -> List[CurrencyResponse]:
        """
        Retrieve all currencies available in FedaPay's system.
        This method fetches a list of all currencies and their details.
        Returns:
            List[CurrencyResponse]: A list of CurrencyResponse objects containing currency details.
        Raises:
            CurrencyError: If the currency retrieval fails or if there is an error in the request.
        """
        
        async with self.get_client() as client:
            response = await client.get(
                endpoint=self.ENDPOINTS["get_all_currencies"],
                headers=self.get_headers(authorization=True)
            )
                        
            if response.status in range(200, 300):
                currencies_data: List[Dict[str, Any]] = response.data.get("v1/currencies", [])
                return [
                    CurrencyResponse(
                        currency_id=currency.get("id"),
                        name=currency.get("name"),
                        provider=self.provider_name(),
                        iso=currency.get("iso"),
                        created_at=parser.parse(currency.get("created_at")),
                        updated_at=parser.parse(currency.get("updated_at")),
                        modes=currency.get("modes", []),
                        raw_response=response.data,
                    ) for currency in currencies_data
                ]
        
            raise CurrencyError(
                message="Failed to fetch all currencies",
                status_code=response.status,
                raw_response=response.data
            )
    
    ############################
    #####    Log Methods    ####
    ############################
    def _build_log_detail(
        self, 
        data: Dict[str, Any], 
        raw_response: Optional[Dict[str, Any]] = None,
    ) -> LogDetail:
        """
        Build a LogDetail object from the FedaPay API response data.
        Args:
            data (Dict[str, Any]): The raw data from the FedaPay API response.
            raw_response (Optional[Dict[str, Any]]): The full raw response data.
        Returns:
            LogDetail: The log details.
        Raises:
        
        """
        
        return LogDetail(
            id=data.get("id"),
            method=data.get("method"),
            url=data.get("url"),
            status=str(data.get("status")),  # status can be int or str, force str
            ip_address=data.get("ip_address"),
            version=data.get("version"),
            provider=Provider.FEDAPAY,
            source=data.get("source"),
            query=data.get("query"),
            body=data.get("body"),
            response=data.get("response"),
            account_id=str(data.get("account_id")) if data.get("account_id") is not None else None,
            created_at=parser.parse(data.get("created_at")),
            updated_at=parser.parse(data.get("updated_at")),
            metadata={k: v for k, v in data.items() if k not in {
                "id", "method", "url", "status", "ip_address", "version", "provider", "source",
                "query", "body", "response", "account_id", "created_at", "updated_at"
            }},
            raw_response=raw_response if raw_response else data
        )

    async def get_all_logs(self) -> LogsResponse:
        """
        Retrieve all logs from FedaPay's system.
        This method fetches a list of logs and their details.
        Returns:
            LogsResponse: The response containing a list of logs and pagination metadata.
        Raises:
            LogError: If the log retrieval fails or if there is an error in the request.
        """
        
        async with self.get_client() as client:
            response = await client.get(
                endpoint=self.ENDPOINTS["get_all_logs"],
                headers=self.get_headers(authorization=True)
            )
            
            if response.status in range(200, 300):
                logs_data: List[Dict[str, Any]] = response.data.get("v1/logs", [])                
                meta_data: Dict[str, Any] = response.data.get("meta", {})
                logs = [
                    self._build_log_detail(log)
                    for log in logs_data
                ]
                meta = PaginationMeta(
                    current_page=meta_data.get("current_page"),
                    next_page=meta_data.get("next_page"),
                    prev_page=meta_data.get("prev_page"),
                    per_page=meta_data.get("per_page"),
                    total_pages=meta_data.get("total_pages"),
                    total_count=meta_data.get("total_count"),
                )
                return LogsResponse(logs=logs, meta=meta)
        
            raise LogError(
                message="Failed to fetch all logs",
                status_code=response.status,
                raw_response=response.data
            )
    
    ############################
    ##### Webhook Methods   ####
    ############################
    def get_webhook_secret(self) -> str:
        """Get the webhook secret for FedaPay."""
        
        secret = self.config.extra.get("webhook_secret")
        if not secret:
            raise WebhookValidationError("Webhook secret is missing in configuration")
        return secret
        
    def compare_signatures(
        self, 
        payload_str: str, 
        received_signature: str, 
    ) -> bool:
        """
        Compare the computed signature with the one in the headers, using a secure comparison.
        Args:
            payload_str (str): The string representation of the payload.
            received_signature (str): The signature received in the headers.
        Returns:
            bool: True if the signatures match, False otherwise.
        Raises:
            AuthenticationError: If the webhook secret is not configured or if the signatures do not match.
        """
        
        webhook_secret = self.get_webhook_secret()

        computed_signature = hmac.new(
            key=webhook_secret.encode('utf-8'),
            msg=payload_str.encode('utf-8'),
            digestmod=hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(computed_signature, received_signature):
            raise AuthenticationError("Invalid signature")

        return True

    def validate_webhook(self, payload: Dict[str, str], headers: Dict[str, str]) -> bool:
        """
        Validate the webhook payload and headers received from FedaPay.
        Args:
            payload (Dict[str, Any]): The webhook payload received from FedaPay.
            headers (Dict[str, str]): The headers received with the webhook.
        Returns:
            bool: True if the webhook is valid, False otherwise.
        Raises:
            AuthenticationError: If the webhook signature is invalid or if required headers are missing.
            WebhookValidationError: If the payload or headers are invalid.
        """
               
        signature_header = headers.get("X-Fedapay-Signature")
        if not signature_header:
            raise AuthenticationError("Missing signature header")
        
        timestamp = None
        signature = None

        for item in signature_header.split(','):
            try:
                key, value = item.split('=')
                if key == 't':
                    timestamp = int(value)
                elif key == 's':
                    signature = value
            except ValueError:
                continue

        if timestamp is None or signature is None:
            raise WebhookValidationError("Invalid signature format")

        raw_payload_str = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
        signed_payload = f"{timestamp}.{raw_payload_str}"

        return self.compare_signatures(signed_payload, signature)

    async def parse_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> WebhookEvent:
        """
        Parse the webhook payload and headers to create a WebhookEvent object.
        Args:
            payload (Dict[str, Any]): The webhook payload received from FedaPay.
            headers (Dict[str, str]): The headers received with the webhook.
        Returns:
            WebhookEvent: An object representing the parsed webhook event.
        Raises:
            AuthenticationError: If the webhook signature is invalid or if required headers are missing.
        """        
        if not self.validate_webhook(payload, headers):
            raise AuthenticationError(
                message="Invalid webhook signature",
            )
        
        event_type = payload.get("name")  # e.g. "transaction.created"
        entity: Dict[str, Any] = payload.get("entity", {})

        # Mapping currency_id -> ISO
        currency_id = int(entity.get("currency_id"))
        currency_iso = FedapayCurrencyMapper.get_iso(currency_id) if currency_id else "XOF"

        # Normalize the status
        raw_status = entity.get("status")
        normalized_status = self.get_normalize_status(raw_status)

        # Extract standard fields and metadata
        standard_fields = {
            "id", 
            "name", 
            "amount", 
            "status",
            "created_at",
            "currency_id", 
        }
        metadata = {k: v for k, v in entity.items() if k not in standard_fields}

        # Add FedaPay's metadata if available
        if entity.get("metadata"):
            metadata["fedapay_metadata"] = entity["metadata"]

        return WebhookEvent(
            event_type=event_type,
            provider=self.provider_name(),
            transaction_id=str(entity.get("id")),
            status=normalized_status,
            amount=float(entity.get("amount", 0)),
            currency=Currency(currency_iso),
            created_at=parser.parse(entity.get("created_at")),
            raw_data=payload,
            metadata=metadata,
        )

    def _build_webhook_detail(
        self, 
        data: Dict[str, Any], 
        raw_response: Optional[Dict[str, Any]] = None
    ) -> WebhookDetail:
        """
        Build a WebhookDetail object from the FedaPay API response data.
        Args:
            data (Dict[str, Any]): The raw data from the FedaPay API response.
            response_status (int): The HTTP status code of the response.
            raw_response (Optional[Dict[str, Any]]): The full raw response data.
        Returns:
            WebhookDetail: The webhook details.
        Raises:
            WebhookError: If the webhook data is invalid or if there is an error in the request.
        """
        
        return WebhookDetail(
            id=int(data.get("id")),
            url=data.get("url"),
            enabled=data.get("enabled"),
            ssl_verify=data.get("ssl_verify"),
            disable_on_error=data.get("disable_on_error"),
            account_id=int(data.get("account_id")),
            http_headers=data.get("http_headers"),
            created_at=parser.parse(data.get("created_at")),
            updated_at=parser.parse(data.get("updated_at")),
            provider=self.provider_name(),        
            metadata={k: v for k, v in data.items() if k not in {
                "id", "url", "enabled", "ssl_verify", "disable_on_error", "account_id",
                "http_headers",  "created_at", "updated_at", "provider"
            }},
            raw_response=raw_response
        )
    
    async def get_all_webhooks(self) -> WebhooksResponse:
        """
        Retrieve all webhooks from FedaPay's system.
        This method fetches a list of webhooks and their details.
        Returns:
            WebhooksResponse: The response containing a list of webhooks and pagination metadata.
        Raises:
            WebhookError: If the webhook retrieval fails or if there is an error in the request.
        """
        
        async with self.get_client() as client:
            response = await client.get(
                endpoint=self.ENDPOINTS["get_all_webhooks"],
                headers=self.get_headers(authorization=True)
            )
            
            if response.status in range(200, 300):
                webhooks_data: Dict[str, Any] = response.data.get("v1/webhooks", {})
                meta_data: Dict[str, Any] = response.data.get("meta", {})
                webhooks = [
                    self._build_webhook_detail(webhook, response.data)
                    for webhook in webhooks_data
                ]
                meta = PaginationMeta(
                    current_page=meta_data.get("current_page"),
                    next_page=meta_data.get("next_page"),
                    prev_page=meta_data.get("prev_page"),
                    per_page=meta_data.get("per_page"),
                    total_pages=meta_data.get("total_pages"),
                    total_count=meta_data.get("total_count"),
                )
                return WebhooksResponse(webhooks=webhooks, meta=meta)
        
            raise WebhookError(
                message="Failed to fetch all webhooks",
                status_code=response.status,
                raw_response=response.data
            )
    
    async def get_webhook_detail(self, webhook_id: str) -> WebhookDetail:
        """
        Retrieve the details of a specific webhook by its ID.
        Args:
            webhook_id (str): The ID of the webhook to retrieve.
        Returns:
            WebhookDetail: An object containing the webhook's details.
        Raises:
            WebhookError: If the webhook cannot be found or if there is an error in the request.
        """
        
        async with self.get_client() as client:
            response = await client.get(
                endpoint=self.ENDPOINTS["get_webhook"].format(id=webhook_id),
                headers=self.get_headers(authorization=True)
            )
            
            if response.status in range(200, 300):
                webhook_data: Dict[str, Any] = response.data.get("v1/webhook", {})
                return self._build_webhook_detail(webhook_data, response.data)
        
            raise WebhookError(
                message=f"Failed to fetch webhook with ID {webhook_id}",
                status_code=response.status,
                raw_response=response.data
            )
