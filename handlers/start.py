from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from keyboards.inline import get_main_keyboard
from database.db import get_user_data

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user_data = await get_user_data(message.from_user.id)
    text = "👋 Welcome to Report Bot!\n\n"
    if user_data and user_data.get('session_id'):
        text += "✅ You have already configured your session.\n"
    else:
        text += "❌ No session configured. Use /set_session first.\n"
    text += "\nUse the buttons below:"
    await message.answer(text, reply_markup=get_main_keyboard())

@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = """
📌 *Commands:*
/start - Show main menu
/set_session - Set Instagram session ID
/set_target - Set target username
/select_types - Choose report types
/report - Start reporting
/my_data - Show my configuration
/cancel - Cancel current operation

*Admin commands:*
/stats - Bot statistics
/broadcast - Send message to all users
/logs - Get recent logs
/restart - Restart bot (dev only)
"""
    await message.answer(help_text, parse_mode="Markdown")

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("✅ Operation cancelled.", reply_markup=get_main_keyboard())