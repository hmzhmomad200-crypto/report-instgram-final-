from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from states.states import SessionState
from database.db import save_session, get_user_data
from utils.instagram_reporter import InstagramReporter
from keyboards.inline import get_main_keyboard

router = Router()
reporter = InstagramReporter()

@router.message(Command("set_session"))
async def cmd_set_session(message: Message, state: FSMContext):
    await state.set_state(SessionState.waiting_for_session)
    await message.answer("📝 Please send your Instagram session ID (sessionid cookie):\n\nYou can find it in browser cookies after logging in.")

@router.message(SessionState.waiting_for_session)
async def receive_session(message: Message, state: FSMContext):
    session_id = message.text.strip()
    if not session_id:
        await message.answer("❌ Empty session ID. Send a valid session or /cancel.")
        return
    
    msg = await message.answer("🔄 Validating session...")
    username = await reporter.validate_session(session_id)
    
    if username:
        await save_session(message.from_user.id, session_id, username)
        await msg.edit_text(f"✅ Session validated!\nLogged in as: @{username}\nSession saved.")
        await state.clear()
        await message.answer("Main menu:", reply_markup=get_main_keyboard())
    else:
        await msg.edit_text("❌ Invalid session ID. Please check and try again.\nUse /cancel to abort.")

@router.callback_query(F.data == "set_session")
async def cb_set_session(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await cmd_set_session(callback.message, state)
    await callback.message.delete()