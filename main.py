"""
Main Application Entry Point.
FastAPI server that manages the Telegram webhook and Razorpay callbacks.
Also handles bot initialization and the background scheduler.
"""
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from loguru import logger

from config import settings
from db.connection import init_db, close_db
from bot import build_bot
from services.scheduler import start_scheduler, stop_scheduler, set_bot_app


# Initialize logs
logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>")

# Global bot application instance
bot_app = build_bot()
set_bot_app(bot_app)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI."""
    logger.info("🚀 Starting ApplixyBot...")

    # 1. Init Database
    await init_db()

    # 2. Start Bot
    await bot_app.initialize()
    if settings.ENVIRONMENT == "production":
        import os
        webhook = settings.WEBHOOK_URL or os.getenv("RAILWAY_PUBLIC_DOMAIN") or ""
        if not webhook:
            raise ValueError("CRITICAL: WEBHOOK_URL is missing. Please set it in Railway variables!")
            
        webhook = webhook if webhook.startswith("http") else f"https://{webhook}"
        webhook = webhook.rstrip('/')
        
        logger.info(f"Setting webhook URL: {webhook}")
        await bot_app.bot.set_webhook(url=f"{webhook}/telegram-webhook")
    else:
        logger.info("Polling mode enabled (development).")
        # In dev, we start polling natively
        await bot_app.updater.start_polling(drop_pending_updates=True)
    await bot_app.start()

    # 3. Start Background Scheduler
    start_scheduler()

    yield

    # Shutdown sequence
    logger.info("🛑 Shutting down ApplixyBot...")
    stop_scheduler()
    
    
    # We consciously avoid deleting the webhook on production shutdown 
    # to prevent breaking Railway's zero-downtime deploys when the old container dies.
    if settings.ENVIRONMENT != "production":
        await bot_app.updater.stop()
        
    await bot_app.stop()
    await bot_app.shutdown()
    await close_db()


# FastAPI App
app = FastAPI(title="ApplixyBot API", lifespan=lifespan)


@app.get("/health")
async def health_check():
    """Railway healthcheck endpoint."""
    return {"status": "ok", "bot": "ApplixyBot"}


from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint — serves Razorpay compliance landing page."""
    from pathlib import Path
    html_path = Path(__file__).parent / "templates" / "index.html"
    return html_path.read_text(encoding="utf-8")


@app.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    """Receive updates from Telegram in production."""
    if settings.ENVIRONMENT != "production":
        return {"status": "ignored", "reason": "Not in production mode"}
    
    from telegram import Update
    json_data = await request.json()
    update = Update.de_json(json_data, bot_app.bot)
    
    # Log what we received
    update_type = "unknown"
    if update.message:
        update_type = f"message: {update.message.text or '(non-text)'}"
    elif update.callback_query:
        update_type = f"callback: {update.callback_query.data}"
    logger.info(f"Webhook received: {update_type} from user {update.effective_user.id if update.effective_user else '?'}")
    
    # Process update with error catching
    try:
        await bot_app.process_update(update)
    except Exception as e:
        logger.error(f"Error processing update: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}
    
    return {"status": "ok"}


@app.post("/razorpay-webhook")
async def razorpay_webhook(request: Request):
    """Handle successful subscription payments."""
    from services.payment_service import verify_webhook_signature, extract_payment_info
    from db.users import update_user_plan
    from datetime import datetime, timezone
    from dateutil.relativedelta import relativedelta # For easily adding 1 month

    # Verify Signature
    signature = request.headers.get("x-razorpay-signature")
    payload = await request.body()

    if not signature or not verify_webhook_signature(payload, signature):
        logger.warning("Invalid Razorpay webhook signature")
        raise HTTPException(status_code=400, detail="Invalid signature")

    data = await request.json()
    
    # We only care about payment.captured or payment_link.paid
    event = data.get("event")
    if event not in ("payment.captured", "payment_link.paid"):
        return {"status": "ignored", "event": event}

    # Extract user info
    payment_info = extract_payment_info(data)
    if not payment_info:
        logger.error(f"Could not extract telegram_id from payment event: {data}")
        return {"status": "error", "message": "Missing reference data"}

    telegram_id = payment_info["telegram_id"]
    plan = payment_info["plan"]

    # Calculate expiration (1 month from now)
    expires_at = datetime.now(timezone.utc) + relativedelta(months=1)

    # Upgrade User in DB
    await update_user_plan(telegram_id, plan, expires_at)

    # Notify User via bot
    try:
        from utils.messages import escape_md
        amount = data.get("payload", {}).get("payment", {}).get("entity", {}).get("amount", 0) / 100
        await bot_app.bot.send_message(
            chat_id=telegram_id,
            text=(
                f"🎉 *Payment Successful\\!*\n\n"
                f"Your account has been upgraded to the *{plan.title()}* plan\\.\n"
                f"Amount paid: ₹{amount}\n"
                f"Valid until: {escape_md(expires_at.strftime('%Y-%m-%d'))}\n\n"
                "Thank you for supporting ApplixyBot\\!\n"
                "Type /menu to explore your new features\\."
            ),
            parse_mode="MarkdownV2"
        )
    except Exception as e:
        logger.error(f"Failed to notify user {telegram_id} of upgrade: {e}")

    return {"status": "ok"}


@app.get("/health")
def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "service": "applixybot"}

if __name__ == "__main__":
    import uvicorn
    # Make sure python-dateutil is added to requirements for relativedelta
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
