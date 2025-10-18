import asyncio
from easyswitch.adapters.orange import OrangeMoneyAdapter

async def main():
    orange = OrangeMoneyAdapter(
        merchant_code="MERCH123",
        api_key="YOUR_API_KEY",
        country_code="ci",
        environment="sandbox"
    )

    response = await orange.send_payment(
        amount=5000,
        phone_number="22507081234",
        currency="XOF",
        reference="order_456"
    )
    print(response)

asyncio.run(main())
