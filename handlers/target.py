from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from states.states import TargetState
from database.db import save_target, get_user_data
from utils.instagram_reporter import InstagramReporter
from keyboards.inline import get_main_keyboard

router = Router()
reporter = InstagramReporter()

@router.message(Command("set_target"))
async def cmd_set_target(message: Message, state: FSMContext):
    user_data = await get_user_data(message.from_user.id)
    if not user_data or not user_data.get('session_id'):
        await message.answer("❌ Please set your session first using /set_session")
        return
    await state.set_state(TargetState.waiting_for_username)
    await message.answer("🎯 Send the target Instagram username (without @)")

@router.message(TargetState.waiting_for_username)
async def receive_target(message: Message, state: FSMContext):
    username = message.text.strip().lstrip('@')
    if not username:
        await message.answer("❌ Username cannot be empty.")
        return
    
    user_data = await get_user_data(message.from_user.id)
    session_id = user_data['session_id']
    
    msg = await message.answer(f"🔍 Fetching user ID for @{username}...")
    target_id = await reporter.get_user_id(username, session_id)
    
    if target_id:
        await save_target(message.from_user.id, username, target_id)
        await msg.edit_text(f"✅ Target set: @{username} (ID: {target_id})")
        await state.clear()
        await message.answer("Main menu:", reply_markup=get_main_keyboard())
    else:
        await msg.edit_text(f"❌ Could not find user @{username}. Check spelling or privacy settings.")
        await state.clear()

@router.callback_query(F.data == "set_target")
async def cb_set_target(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    # Fix: use callback.from_user.id not callback.message.from_user.id
    user_data = await get_user_data(callback.from_user.id)
    if not user_data or not user_data.get('session_id'):
        await callback.message.answer("❌ Please set your session first using /set_session")
        return
    await state.set_state(TargetState.waiting_for_username)
    await callback.message.answer("🎯 Send the target Instagram username (without @)")
