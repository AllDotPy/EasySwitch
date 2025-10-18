import httpx
from typing import Dict, Any, Optional

class MTNMobileMoneyAdapter:
    """
    MTN Mobile Money API Adapter
    --------------------------------
    Handles:
    - Authentication (OAuth2)
    - Request-to-Pay (Collections)
    - Transfers (Disbursements)
    - Transaction Status
    - Refunds (if supported)
    """

    BASE_URL = "https://api.mtn.com/v1/"  # Change to sandbox for testing

    def __init__(self, api_key: str, subscription_key: str, environment: str = "sandbox"):
        """
        :param api_key: API Key from MTN Developer Portal
        :param subscription_key: Subscription Key (Ocp-Apim-Subscription-Key)
        :param environment: "sandbox" or "production"
        """
        self.api_key = api_key
        self.subscription_key = subscription_key
        self.environment = environment
        self.access_token = None

    async def authenticate(self) -> str:
        """
        Obtain OAuth2 access token from MTN API.
        """
        url = f"{self.BASE_URL}token/"
        headers = {
            "Ocp-Apim-Subscription-Key": self.subscription_key,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, auth=(self.api_key, ""))
            resp.raise_for_status()
            data = resp.json()
            self.access_token = data.get("access_token")
            return self.access_token

    async def send_payment(self, amount: float, phone_number: str, currency: str, reference: str) -> Dict[str, Any]:
        """
        Initiate a 'Request to Pay' (Collection) transaction.
        """
        if not self.access_token:
            await self.authenticate()

        url = f"{self.BASE_URL}collection/request-to-pay"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Reference-Id": reference,
            "X-Target-Environment": self.environment,
            "Content-Type": "application/json",
            "Ocp-Apim-Subscription-Key": self.subscription_key,
        }

        payload = {
            "amount": str(amount),
            "currency": currency,
            "externalId": reference,
            "payer": {
                "partyIdType": "MSISDN",
                "partyId": phone_number,
            },
            "payerMessage": "EasySwitch Payment",
            "payeeNote": "Thank you for using EasySwitch",
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload)
            return {"status_code": resp.status_code, "reference": reference}

    async def check_transaction_status(self, reference: str) -> Dict[str, Any]:
        """
        Check the status of a transaction by reference ID.
        """
        if not self.access_token:
            await self.authenticate()

        url = f"{self.BASE_URL}transaction/status/{reference}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Ocp-Apim-Subscription-Key": self.subscription_key,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.json()

    async def process_refund(self, original_reference: str, amount: float, currency: str) -> Dict[str, Any]:
        """
        Process refund for a completed transaction (if supported).
        """
        if not self.access_token:
            await self.authenticate()

        url = f"{self.BASE_URL}disbursement/transfer"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Ocp-Apim-Subscription-Key": self.subscription_key,
            "Content-Type": "application/json",
        }

        payload = {
            "amount": str(amount),
            "currency": currency,
            "externalId": f"refund_{original_reference}",
            "payee": {"partyIdType": "MSISDN", "partyId": "<customer_number>"},
            "payerMessage": "Refund Processed",
            "payeeNote": "Refund from EasySwitch",
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload)
            return {"status_code": resp.status_code, "refund_reference": original_reference}
