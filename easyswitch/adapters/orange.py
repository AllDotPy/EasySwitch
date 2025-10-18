import httpx
import hmac
import hashlib
from typing import Dict, Any, List, Optional


class OrangeMoneyAdapter:
    """
    Orange Money API Adapter
    --------------------------------
    Supports:
    - Authentication via X-AUTH-TOKEN
    - Single and Bulk Payment Requests
    - Transaction Status Checks
    - Webhook Signature Validation
    """

    def __init__(
        self,
        merchant_code: str,
        api_key: str,
        country_code: str = "ci",  # Default: Côte d'Ivoire
        environment: str = "sandbox"
    ):
        """
        :param merchant_code: Your Orange Money merchant code (e.g., MERCH123)
        :param api_key: API key from Orange Developer Portal
        :param country_code: ISO country code (e.g., 'ci', 'sn', 'ml')
        :param environment: 'sandbox' or 'production'
        """
        self.merchant_code = merchant_code
        self.api_key = api_key
        self.country_code = country_code
        self.environment = environment
        self.auth_token = None

        # Example: https://api.orange.ci/ or https://api.orange.sn/
        self.base_url = f"https://api.orange.{country_code}/"
        if environment == "sandbox":
            self.base_url = f"https://sandbox-api.orange.{country_code}/"

    async def authenticate(self) -> str:
        """
        Obtain X-AUTH-TOKEN for subsequent requests.
        """
        url = f"{self.base_url}api/token"
        headers = {"Content-Type": "application/json"}

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json={"merchant_code": self.merchant_code, "api_key": self.api_key}, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            self.auth_token = data.get("token")
            return self.auth_token

    async def send_payment(
        self,
        amount: float,
        phone_number: str,
        currency: str,
        reference: str
    ) -> Dict[str, Any]:
        """
        Initiate a single payment to a customer.
        """
        if not self.auth_token:
            await self.authenticate()

        url = f"{self.base_url}api/pay"
        headers = {
            "X-AUTH-TOKEN": self.auth_token,
            "Content-Type": "application/json",
        }

        payload = {
            "merchant_code": self.merchant_code,
            "amount": amount,
            "currency": currency,
            "customer_msisdn": phone_number,
            "order_id": reference,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload)
            return {"status_code": resp.status_code, "reference": reference}

    async def send_bulk_payments(
        self,
        payments: List[Dict[str, Any]],
        batch_reference: str
    ) -> Dict[str, Any]:
        """
        Send bulk payments in one request.
        Each item in 'payments' must include:
        {
            "phone_number": "22507081234",
            "amount": 5000,
            "currency": "XOF"
        }
        """
        if not self.auth_token:
            await self.authenticate()

        url = f"{self.base_url}api/bulkpay"
        headers = {
            "X-AUTH-TOKEN": self.auth_token,
            "Content-Type": "application/json",
        }

        payload = {
            "merchant_code": self.merchant_code,
            "batch_reference": batch_reference,
            "transactions": [
                {
                    "customer_msisdn": tx["phone_number"],
                    "amount": tx["amount"],
                    "currency": tx["currency"]
                } for tx in payments
            ]
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload)
            return {"status_code": resp.status_code, "batch_reference": batch_reference}

    async def check_transaction_status(self, reference: str) -> Dict[str, Any]:
        """
        Check the status of a payment using its reference.
        """
        if not self.auth_token:
            await self.authenticate()

        url = f"{self.base_url}api/transaction/status/{reference}"
        headers = {"X-AUTH-TOKEN": self.auth_token}

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    def validate_webhook_signature(payload: str, signature: str, secret: str) -> bool:
        """
        Validate webhook signature sent from Orange Money.

        :param payload: Raw webhook request body
        :param signature: X-Signature header from Orange
        :param secret: Shared secret key from Orange dashboard
        """
        computed_sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(computed_sig, signature)
