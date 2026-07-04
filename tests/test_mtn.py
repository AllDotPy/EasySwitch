import asyncio
from easyswitch.adapters.mtn import MTNMobileMoneyAdapter

async def main():
    mtn = MTNMobileMoneyAdapter(
        api_key="YOUR_API_KEY",
        subscription_key="YOUR_SUBSCRIPTION_KEY",
        environment="sandbox"
    )

    response = await mtn.send_payment(
        amount=10.0,
        phone_number="233541234567",
        currency="GHS",
        reference="order_123"
    )
    print(response)

asyncio.run(main())
