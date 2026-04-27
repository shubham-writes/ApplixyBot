import asyncio
import os
from telegram import Bot
from config import settings
from utils.messages import upgrade_early_adopter_message

async def test():
    bot = Bot(settings.TELEGRAM_BOT_TOKEN)
    pricing = {'early_adopter_price': 199, 'regular_price': 499, 'days_remaining': 30}
    msg = upgrade_early_adopter_message(pricing)
    print("Testing message parsing...")
    try:
        # Just send to the admin to test parsing
        await bot.send_message(chat_id=settings.ADMIN_TELEGRAM_ID, text=msg, parse_mode="MarkdownV2")
        print("Success!")
    except Exception as e:
        print("ERROR:", e)

asyncio.run(test())
