"""
Payment Service — Razorpay integration for subscription management.
"""
import razorpay
from loguru import logger
from config import settings


def _get_client() -> razorpay.Client:
    """Get Razorpay client instance."""
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )


# Plan pricing in paise (1 INR = 100 paise)
PLAN_PRICES = {
    "pro": {"amount": 9900, "name": "Pro", "display": "₹99/month"},
    "proplus": {"amount": 69900, "name": "Pro+", "display": "₹699/month"},
    "premium": {"amount": 149900, "name": "Premium", "display": "₹1,499/month"},
}


async def create_payment_link(
    plan: str,
    telegram_id: int,
    amount: int | None = None,
    is_early_adopter: bool = False,
) -> str | None:
    """
    Create a Razorpay payment link for a subscription plan.

    Args:
        plan: Plan identifier (pro)
        telegram_id: User's Telegram ID (for reference tracking)
        amount: Price in INR (dynamic from pricing service). Falls back to PLAN_PRICES.
        is_early_adopter: Whether this is an early adopter payment (passed to webhook).

    Returns:
        Payment URL string, or None on failure
    """
    if plan not in PLAN_PRICES and amount is None:
        logger.error(f"Invalid plan: {plan}")
        return None

    plan_info = PLAN_PRICES.get(plan, {"name": "Pro"})
    amount_paise = (amount * 100) if amount else plan_info.get("amount", 9900)
    display_price = f"₹{amount}" if amount else plan_info.get("display", "₹99")

    try:
        import time
        client = _get_client()
        unique_ref = f"applixy_{telegram_id}_{plan}_{int(time.time())}"
        payment_link = client.payment_link.create({
            "amount": amount_paise,
            "currency": "INR",
            "description": f"ApplixyBot Pro Plan — 1 Month Access ({display_price})",
            "reference_id": unique_ref,
            "notes": {
                "telegram_id": str(telegram_id),
                "plan": plan,
                "is_early_adopter": "true" if is_early_adopter else "false",
            }
        })

        url = payment_link.get("short_url")
        logger.info(f"Payment link created for user {telegram_id}, plan {plan}, amount={display_price}, early={is_early_adopter}: {url}")
        return url

    except Exception as e:
        logger.error(f"Failed to create payment link: {e}")
        return None


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    Verify Razorpay webhook signature.

    Args:
        payload: Raw request body bytes
        signature: X-Razorpay-Signature header value

    Returns:
        True if signature is valid
    """
    try:
        client = _get_client()
        client.utility.verify_webhook_signature(
            payload.decode("utf-8"),
            signature,
            settings.RAZORPAY_WEBHOOK_SECRET,
        )
        return True
    except Exception as e:
        logger.error(f"Webhook signature verification failed: {e}")
        return False


def extract_payment_info(webhook_data: dict) -> dict | None:
    """
    Extract telegram_id and plan from Razorpay webhook payload.

    Returns:
        {telegram_id: int, plan: str} or None
    """
    try:
        entity = webhook_data.get("payload", {}).get("payment_link", {}).get("entity", {})
        notes = entity.get("notes", {})
        telegram_id = int(notes.get("telegram_id", 0))
        plan = notes.get("plan", "")

        if telegram_id and plan in PLAN_PRICES:
            return {"telegram_id": telegram_id, "plan": plan}

        # Try alternate path for payment entity
        payment = webhook_data.get("payload", {}).get("payment", {}).get("entity", {})
        notes = payment.get("notes", {})
        telegram_id = int(notes.get("telegram_id", 0))
        plan = notes.get("plan", "")

        if telegram_id and plan in PLAN_PRICES:
            return {"telegram_id": telegram_id, "plan": plan}

    except Exception as e:
        logger.error(f"Failed to extract payment info: {e}")

    return None
