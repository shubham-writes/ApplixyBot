"""
Upgrade and Payment handlers.
"""
from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger

from db.users import get_user
from services.payment_service import create_payment_link
from utils import keyboards, messages
from utils.helpers import escape_md


async def upgrade_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /upgrade."""
    user_id = update.effective_user.id
    user = await get_user(user_id)

    if not user:
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text("Please /start first.")
        else:
            await update.message.reply_text("Please /start first.")
        return

    plan = user.get("plan", "free")
    msg = messages.upgrade_plans(plan)
    kb = keyboards.upgrade_keyboard()

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(msg, reply_markup=kb, parse_mode="MarkdownV2")
    else:
        await update.message.reply_text(msg, reply_markup=kb, parse_mode="MarkdownV2")


async def checkout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate and send Razorpay payment link."""
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton

    query = update.callback_query
    await query.answer()

    # callback_data: upgrade_pro / upgrade_proplus / upgrade_premium
    raw = query.data  # e.g. "upgrade_proplus"
    plan = raw[len("upgrade_"):]  # strip leading "upgrade_" prefix
    user_id = update.effective_user.id

    back_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back to Plans", callback_data="menu_upgrade")]
    ])

    try:
        await query.edit_message_text("⏳ Generating secure payment link...")

        url = await create_payment_link(plan, user_id)

        if url:
            plan_display = {"pro": "Pro", "proplus": "Pro+", "premium": "Premium"}.get(plan, plan.title())
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"💳 Pay for {plan_display} — Tap Here", url=url)],
                [InlineKeyboardButton("🔙 Back to Plans", callback_data="menu_upgrade")]
            ])

            safe_plan = escape_md(plan_display)
            await query.edit_message_text(
                f"✅ *Your payment link is ready\\!*\n\n"
                f"Tap the button below to upgrade to *{safe_plan}* securely via Razorpay\\.\n\n"
                "Your account upgrades automatically within 1 minute of payment\\.",
                reply_markup=kb,
                parse_mode="MarkdownV2"
            )
        else:
            await query.edit_message_text(
                "❌ Could not generate a payment link\\. Please try again\\.",
                reply_markup=back_kb,
                parse_mode="MarkdownV2"
            )

    except Exception as e:
        logger.error(f"checkout_handler crashed for plan={plan} user={user_id}: {e}")
        try:
            await query.edit_message_text(
                "❌ Something went wrong\\. Please try again\\.",
                reply_markup=back_kb,
                parse_mode="MarkdownV2"
            )
        except Exception:
            pass
