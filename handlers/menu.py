"""
Main Menu handler — /menu command and back_menu callback.
"""
from telegram import Update
from telegram.ext import ContextTypes
from utils import keyboards, messages
from db.users import get_user


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /menu command."""
    user = await get_user(update.effective_user.id)
    plan = user.get("plan", "free") if user else "free"
    
    await update.message.reply_text(
        messages.main_menu(user),
        reply_markup=keyboards.main_menu_keyboard(plan),
        parse_mode="MarkdownV2",
    )


async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle 'Back to Menu' callback button."""
    query = update.callback_query
    await query.answer()
    user = await get_user(update.effective_user.id)
    plan = user.get("plan", "free") if user else "free"
    
    await query.edit_message_text(
        messages.main_menu(user),
        reply_markup=keyboards.main_menu_keyboard(plan),
        parse_mode="MarkdownV2",
    )
