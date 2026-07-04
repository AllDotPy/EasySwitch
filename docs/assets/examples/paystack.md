# 💳 Paystack Adapter Usage Example

This guide demonstrates how to use the **`PaystackAdapter`** in **EasySwitch** to initialize, verify, and manage payments through [Paystack](https://paystack.com).

---

## ⚙️ Setup

Make sure you have **EasySwitch** installed:

```python
# Using pip
pip install easyswitch

# Or using uv
uv add easyswitch
```

Then export your Paystack secret key as an environment variable:
```python
export EASYSWITCH_PAYSTACK_SECRET_KEY=sk_test_yourkeyhere
```

## 🧠 Configuration Example

Using `EasySwitch.from_dict()` **(unified-multi-provider usage)**
```python
from easyswitch import EasySwitch, Provider

client = EasySwitch.from_dict({
    "providers": {
        Provider.PAYSTACK: {
            "api_key": "sk_test_yourkeyhere",
            "environment": "sandbox",
            "callback_url": "https://example.com/callback",
            "return_url": "https://example.com/return",
            "timeout": 30
        }
    }
})
```

## 💡 Example: Initialize a Payment
Using the EasySwitch client
```python
# Assuming client = EasySwitch.from_dict(...) as shown earlier
from easyswitch.types import TransactionDetail, CustomerInfo, Currency, Provider

tx = TransactionDetail(
    transaction_id="tx_example_001",
    amount=500.0,  # 500.00 NGN (adapter converts to kobo)
    currency=Currency.NGN,
    customer=CustomerInfo(email="customer@example.com", phone_number="+2348012345678"),
    reference="ref_example_001", # unique per payment
    provider=Provider.PAYSTACK
)

res = await client.send_payment(tx)   
print("Link:", res.payment_link)
```

## 🔍 Check status / get transaction detail / refunds

```python
# check status (by reference)
status_resp = await client.check_status("ref_example_001")
print("Status:", status_resp.status)   # TransactionStatus enum
print("Amount:", status_resp.amount)

# get full transaction details (by transaction id)
tx_detail = await client.get_transaction_detail("123456789")  
print(tx_detail.status, tx_detail.amount, tx_detail.customer.email)

# refund (pass transaction id and optional amount in main units)
refund_resp = await client.refund(transaction_id="123456789", amount=100.0)
print("Refund status:", refund_resp.status, "amount:", refund_resp.amount)
```

## ⚠️ Notes
- Test Mode:
 Use your sk_test_... key for sandbox testing. You’ll get URLs like:
```python
 https://checkout.paystack.com/abcd1234
```

- Live Mode:
 When you switch to a live key (sk_live_...), your URLs will look like:
```python
 https://paystack.com/pay/your-page-id
```

- Reference Uniqueness:
Each transaction must have a unique reference string.

- Timeouts:
The timeout in your config controls how long the adapter waits for a Paystack response.


## 🧰 Troubleshooting
| Error | Cause | Fix |
| :--- | :--- | :--- |
| `PaymentError: 400` | Invalid reference or payload | Ensure **API keys** are correct and **callback URL** is valid. (Often caused by missing or improperly formatted required data). |
| `TimeoutError` | Paystack unresponsive or network delay | Increase `config.timeout` (e.g., from 30 to 60 seconds). |


## 🔗 Related Documentation
- [Paystack API Reference](https://paystack.com/docs/api/)
- [EasySwitch Core Reference](https://alldotpy.github.io/EasySwitch/)
