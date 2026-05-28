import asyncio
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from keyboards.inline import get_report_types_keyboard, get_main_keyboard
from database.db import get_user_data, save_report_types, log_report
from services.report_service import ReportService
from states.states import ReportState
from utils.instagram_reporter import REPORT_TYPES

router = Router()
report_service = ReportService()

def get_loop_count_keyboard():
    buttons = [
        [InlineKeyboardButton(text="🔁 10 times", callback_data="loop:10")],
        [InlineKeyboardButton(text="🔁 30 times", callback_data="loop:30")],
        [InlineKeyboardButton(text="🔁 50 times", callback_data="loop:50")],
        [InlineKeyboardButton(text="🔁 100 times", callback_data="loop:100")],
        [InlineKeyboardButton(text="✏️ Custom...", callback_data="loop:custom")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirmation_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Confirm", callback_data="confirm_yes")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="confirm_no")],
    ])

@router.message(Command("select_types"))
async def cmd_select_types(message: Message, state: FSMContext):
    user_data = await get_user_data(message.from_user.id)
    if not user_data or not user_data.get('session_id'):
        await message.answer("❌ Please set session first using /set_session")
        return
    if not user_data.get('target_id'):
        await message.answer("❌ Please set target first using /set_target")
        return
    selected = user_data.get('report_types', '').split(',') if user_data.get('report_types') else []
    await state.update_data(selected_types=selected)
    await state.set_state(ReportState.selecting_types)
    await message.answer("Select report types (tap to toggle, Done when ready):", 
                         reply_markup=get_report_types_keyboard(selected))

@router.callback_query(F.data == "select_types")
async def cb_select_types(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user_data = await get_user_data(callback.from_user.id)
    if not user_data or not user_data.get('session_id'):
        await callback.message.answer("❌ Please set session first")
        return
    if not user_data.get('target_id'):
        await callback.message.answer("❌ Please set target first")
        return
    selected = user_data.get('report_types', '').split(',') if user_data.get('report_types') else []
    await state.update_data(selected_types=selected)
    await state.set_state(ReportState.selecting_types)
    await callback.message.answer("Select report types (tap to toggle, Done when ready):", 
                                  reply_markup=get_report_types_keyboard(selected))

@router.callback_query(F.data.startswith("toggle_type:"))
async def cb_toggle_type(callback: CallbackQuery, state: FSMContext):
    key = callback.data.split(":")[1]
    data = await state.get_data()
    selected = data.get("selected_types", [])
    if key in selected:
        selected.remove(key)
    else:
        selected.append(key)
    await state.update_data(selected_types=selected)
    await callback.message.edit_reply_markup(reply_markup=get_report_types_keyboard(selected))
    await callback.answer()

@router.callback_query(F.data == "types_done")
async def cb_types_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected_types", [])
    if not selected:
        await callback.answer("No types selected!", show_alert=True)
        return
    selected_str = ",".join(selected)
    await save_report_types(callback.from_user.id, selected_str)
    await callback.message.edit_text(f"✅ Saved {len(selected)} report types.")
    # الانتقال إلى اختيار عدد التكرارات
    await state.set_state(ReportState.selecting_loop_count)
    await callback.message.answer("🔁 How many times do you want to repeat the reports?",
                                  reply_markup=get_loop_count_keyboard())

@router.callback_query(F.data.startswith("loop:"))
async def cb_loop_choice(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    choice = callback.data.split(":")[1]
    if choice == "custom":
        await callback.message.answer("📝 Please enter the number of repetitions (1-500):")
        return
    loop_count = int(choice)
    await state.update_data(loop_count=loop_count)
    await state.set_state(None)
    await _send_report_confirmation(callback.message, callback.from_user.id, loop_count)

@router.message(ReportState.selecting_loop_count)
async def receive_custom_loop(message: Message, state: FSMContext):
    try:
        loop_count = int(message.text.strip())
        if loop_count < 1 or loop_count > 500:
            await message.answer("❌ Please enter a number between 1 and 500.")
            return
        await state.update_data(loop_count=loop_count)
        await state.set_state(None)
        await _send_report_confirmation(message, message.from_user.id, loop_count)
    except ValueError:
        await message.answer("❌ Invalid number. Please enter a valid number (1-500).")

async def _send_report_confirmation(target, user_id: int, loop_count: int):
    user_data = await get_user_data(user_id)
    if not user_data or not user_data.get('session_id'):
        await target.answer("❌ No session set. Use /set_session")
        return
    if not user_data.get('target_id'):
        await target.answer("❌ No target set. Use /set_target")
        return
    if not user_data.get('report_types'):
        await target.answer("❌ No report types selected. Use /select_types")
        return
    report_keys = user_data['report_types'].split(',')
    target_username = user_data['target_username']
    total_reports = len(report_keys) * loop_count
    confirm_text = (f"⚠️ <b>Confirm Report</b>\n\n"
                    f"Target: @{target_username}\n"
                    f"Report types: {len(report_keys)}\n"
                    f"Loop count: {loop_count}\n"
                    f"<b>Total reports to send: {total_reports}</b>\n\n"
                    f"This may take a while. Continue?")
    await target.answer(confirm_text, reply_markup=get_confirmation_keyboard())

@router.callback_query(F.data == "confirm_yes")
async def cb_confirm_yes(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id
    user_data = await get_user_data(user_id)
    if not user_data:
        await callback.message.edit_text("❌ Configuration missing. Start over with /start")
        return
    report_keys = user_data['report_types'].split(',')
    session_id = user_data['session_id']
    target_id = user_data['target_id']
    
    state_data = await state.get_data()
    loop_count = state_data.get('loop_count', 1)
    total_reports = len(report_keys) * loop_count
    progress_msg = await callback.message.edit_text(f"🔄 Starting reports...\n0/{total_reports} completed (loop {loop_count}x)")
    
    success_total = 0
    failed_total = 0
    current_total = 0
    
    for loop_index in range(1, loop_count + 1):
        for idx, key in enumerate(report_keys, 1):
            report_type = REPORT_TYPES[key]
            success = await report_service.report(target_id, session_id, report_type)
            if success:
                success_total += 1
            else:
                failed_total += 1
            current_total += 1
            status = "✅" if success else "❌"
            text = (f"🔄 Progress: {current_total}/{total_reports}\n"
                    f"Loop {loop_index}/{loop_count}\n"
                    f"Last: {status} {report_type['name']}")
            try:
                await progress_msg.edit_text(text)
            except Exception:
                pass
            await log_report(user_id, report_type['name'], success)
            await asyncio.sleep(3)  # تأخير 3 ثوانٍ بين كل بلاغ
    
    final_text = f"✅ Reporting completed!\nSuccess: {success_total}\nFailed: {failed_total}\nTotal: {total_reports} (loops: {loop_count})"
    await progress_msg.edit_text(final_text)
    await callback.message.answer("Main menu:", reply_markup=get_main_keyboard())
    await state.clear()

@router.callback_query(F.data == "confirm_no")
async def cb_confirm_no(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text("❌ Reporting cancelled.")
    await callback.message.answer("Main menu:", reply_markup=get_main_keyboard())
    await state.clear()

@router.callback_query(F.data == "my_data")
async def cb_my_data(callback: CallbackQuery):
    await callback.answer()
    user_data = await get_user_data(callback.from_user.id)
    if not user_data:
        text = "No data found. Use /start to configure."
    else:
        text = f"📊 <b>Your Configuration</b>\n"
        text += f"Session: {'✅' if user_data.get('session_id') else '❌'}\n"
        text += f"Username: @{user_data.get('username') or 'N/A'}\n"
        text += f"Target: @{user_data.get('target_username') or 'Not set'}\n"
        text += f"Report types: {len(user_data.get('report_types', '').split(',')) if user_data.get('report_types') else 0}\n"
    await callback.message.answer(text, reply_markup=get_main_keyboard())
