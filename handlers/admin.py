from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from config import ADMIN_IDS
from database.db import get_stats, get_all_user_ids
from utils.logger import logger
from states.states import BroadcastState

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    stats = await get_stats()
    text = f"📊 <b>Bot Statistics</b>\n\nUsers: {stats['users']}\nTotal reports: {stats['total_reports']}\nSuccessful reports: {stats['success_reports']}"
    await message.answer(text)

@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(BroadcastState.waiting_for_message)
    await message.answer("Send the broadcast message (HTML allowed). /cancel to abort.")

@router.message(BroadcastState.waiting_for_message)
async def broadcast_message(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    user_ids = await get_all_user_ids()
    sent = 0
    failed = 0
    status_msg = await message.answer(f"📤 Sending to {len(user_ids)} users...")
    for uid in user_ids:
        try:
            await message.bot.send_message(uid, message.text or message.caption or "")
            sent += 1
        except Exception:
            failed += 1
    await status_msg.edit_text(f"✅ Broadcast done.\nSent: {sent}\nFailed: {failed}")

@router.message(Command("logs"))
async def cmd_logs(message: Message):
    if not is_admin(message.from_user.id):
        return
    try:
        with open("logs/bot.log", "r", encoding="utf-8") as f:
            lines = f.readlines()[-50:]
            log_text = "".join(lines)
            if len(log_text) > 4000:
                log_text = log_text[-4000:]
            await message.answer(f"<pre>{log_text}</pre>")
    except Exception as e:
        await message.answer(f"Error reading logs: {e}")

@router.message(Command("restart"))
async def cmd_restart(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("Restarting bot...")
    raise SystemExit("Restart requested by admin")
