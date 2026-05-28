import asyncio
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from keyboards.inline import get_report_types_keyboard, get_confirmation_keyboard, get_main_keyboard
from database.db import get_user_data, save_report_types, log_report
from services.report_service import ReportService

router = Router()
report_service = ReportService()

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
    await message.answer("Select report types (tap to toggle, Done when ready):", reply_markup=get_report_types_keyboard(selected))

@router.callback_query(F.data == "select_types")
async def cb_select_types(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user_data = await get_user_data(callback.from_user.id)
    if not user_data or not user_data.get('session_id'):
        await callback.message.answer("❌ Please set session first using /set_session")
        return
    if not user_data.get('target_id'):
        await callback.message.answer("❌ Please set target first using /set_target")
        return
    selected = user_data.get('report_types', '').split(',') if user_data.get('report_types') else []
    await state.update_data(selected_types=selected)
    await callback.message.answer("Select report types (tap to toggle, Done when ready):", reply_markup=get_report_types_keyboard(selected))

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
    await state.clear()
    await callback.message.answer("Main menu:", reply_markup=get_main_keyboard())

async def _send_report_confirmation(target: object, user_id: int):
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
    confirm_text = f"⚠️ <b>Confirm Report</b>\n\nTarget: @{target_username}\nReport types: {len(report_keys)}\n\nThis will send {len(report_keys)} reports. Continue?"
    await target.answer(confirm_text, reply_markup=get_confirmation_keyboard())

@router.message(Command("report"))
async def cmd_report(message: Message):
    await _send_report_confirmation(message, message.from_user.id)

@router.callback_query(F.data == "start_report")
async def cb_start_report(callback: CallbackQuery):
    await callback.answer()
    await _send_report_confirmation(callback.message, callback.from_user.id)

@router.callback_query(F.data == "confirm_yes")
async def cb_confirm_yes(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    user_data = await get_user_data(user_id)
    if not user_data:
        await callback.message.edit_text("❌ Configuration missing. Start over with /start")
        return
    report_keys = user_data['report_types'].split(',')
    session_id = user_data['session_id']
    target_id = user_data['target_id']
    progress_msg = await callback.message.edit_text("🔄 Starting reports...\n0/{} completed".format(len(report_keys)))

    async def progress(current, total, report_name, success):
        status = "✅" if success else "❌"
        text = f"🔄 Progress: {current}/{total}\nLast: {status} {report_name}"
        try:
            await progress_msg.edit_text(text)
        except Exception:
            pass
        await log_report(user_id, report_name, success)

    success, failed = await report_service.run_reports(session_id, target_id, report_keys, progress)
    final_text = f"✅ Reporting completed!\nSuccess: {success}\nFailed: {failed}\nTotal: {len(report_keys)}"
    await progress_msg.edit_text(final_text)
    await callback.message.answer("Main menu:", reply_markup=get_main_keyboard())

@router.callback_query(F.data == "confirm_no")
async def cb_confirm_no(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("❌ Reporting cancelled.")
    await callback.message.answer("Main menu:", reply_markup=get_main_keyboard())

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
