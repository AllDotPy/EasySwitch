# Provider Feature Matrix

## Operations Support

| Operation | CinetPay | PayGate | FedaPay | Semoa | Bizao | Paystack | MTN MoMo | Airtel Money |
|-----------|----------|---------|---------|-------|-------|----------|----------|-------------|
| `send_payment()` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `check_status()` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `get_transaction_detail()` | ❌ | ⚠️¹ | ✅ | ⚠️¹ | ❌ | ✅ | ✅ | ✅ |
| `refund()` | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ (full & partial) | ✅ | ✅ |
| `cancel_transaction()` | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `validate_webhook()` | ✅ | ✅² | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

> ¹ Falls back to `check_status()` with minimal detail.
> ² PayGate validates by checking required fields (no HMAC signature).

## Payment Flow

| Provider | Payment Model | Confirmation |
|----------|--------------|--------------|
| **CinetPay** | Checkout page (redirect) | Webhook + status check |
| **PayGate** | Direct API + Payment link | Webhook + status check |
| **FedaPay** | Checkout page (redirect) | Webhook + status check |
| **Semoa** | API (direct) | Status check |
| **Bizao** | Configurable (web/USSD/TPE) | Status check |
| **Paystack** | Checkout page (redirect) | Webhook + status check |
| **MTN MoMo** | USSD push (async) | Callback webhook |
| **Airtel Money** | USSD push (async) | Webhook + status check |

## Supported Currencies by Provider

| Currency | CinetPay | PayGate | FedaPay | Semoa | Bizao | Paystack | MTN | Airtel |
|----------|----------|---------|---------|-------|-------|----------|-----|--------|
| XOF | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| XAF | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ | ✅ |
| NGN | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| GHS | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| USD | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| EUR | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| UGX | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| TZS | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| KES | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| RWF | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| ZMW | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| MWK | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| BIF | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| ETB | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| BWP | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| CDF | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| GNF | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| KMF | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| ZWL | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |

## Rate Limits

| Provider | Rate Limit Notes |
|----------|-----------------|
| **CinetPay** | Not publicly documented |
| **PayGate** | Not publicly documented |
| **FedaPay** | Typically 60 req/min |
| **Semoa** | Not publicly documented |
| **Bizao** | Contact Bizao support |
| **Paystack** | 50 req/second (varies by plan) |
| **MTN MoMo** | Tiered by subscription plan |
| **Airtel Money** | Contact Airtel support |

## Choosing a Provider

| Use Case | Recommended Provider |
|----------|-------------------|
| **Cards + Mobile Money** | Paystack, FedaPay |
| **West Africa (UEMOA)** | CinetPay, PayGate, Bizao, Semoa |
| **Nigeria** | Paystack |
| **East Africa** | Airtel Money, MTN MoMo |
| **High-volume refunds** | Paystack (full & partial) |
| **USSD/offline channels** | Bizao (TPE/USSD), MTN, Airtel |
| **Simple checkout page** | CinetPay, FedaPay, Paystack |
