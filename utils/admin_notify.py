"""
Admin notification utility.
Sends real-time alerts to the bot owner's Telegram chat.
"""
from loguru import logger
from config import settings


async def notify_admin(bot, message: str) -> None:
    """Send a notification message to the admin. Silently fails if not configured."""
    if not settings.ADMIN_TELEGRAM_ID:
        return
    try:
        await bot.send_message(
            chat_id=settings.ADMIN_TELEGRAM_ID,
            text=message,
            parse_mode="HTML",
        )
    except Exception as e:
        logger.warning(f"Admin notify failed: {e}")
