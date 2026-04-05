import asyncio
from bot import app
from services.scheduler import set_bot_app, _send_daily_alerts
from db.connection import init_db

async def test_alert():
    await init_db()
    set_bot_app(app)
    # The application itself needs to be initialized to send messages
    await app.initialize()
    print("Testing Daily Alerts...")
    await _send_daily_alerts()
    print("Done testing.")

if __name__ == "__main__":
    asyncio.run(test_alert())
