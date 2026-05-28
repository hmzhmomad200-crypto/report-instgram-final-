import asyncio
import random
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from keyboards.inline import get_report_types_keyboard, get_main_keyboard
from database.db import get_user_data, save_report_types, log_report
from services.report_service import ReportService
from states.states import ReportState
from utils.instagram_reporter import REPORT_TYPES

# قائمة بجميع مفاتيح أنواع البلاغات (1 إلى 34)
ALL_TYPES = list(REPORT_TYPES.keys())

router = Router()
report_service = ReportService()

def get_confirmation_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ تأكيد", callback_data="confirm_yes")],
        [InlineKeyboardButton(text="❌ إلغاء", callback_data="confirm_no")],
    ])

@router.message(Command("select_types"))
async def cmd_select_types(message: Message, state: FSMContext):
    user_data = await get_user_data(message.from_user.id)
    if not user_data or not user_data.get('session_id'):
        await message.answer("❌ يرجى تعيين الجلسة أولاً باستخدام /set_session")
        return
    if not user_data.get('target_id'):
        await message.answer("❌ يرجى تعيين الهدف أولاً باستخدام /set_target")
        return
    selected = user_data.get('report_types', '').split(',') if user_data.get('report_types') else []
    await state.update_data(selected_types=selected)
    await state.set_state(ReportState.selecting_types)
    await message.answer("اختر أنواع البلاغات (اضغط على النوع لتحديده، ثم Done عند الانتهاء):", 
                         reply_markup=get_report_types_keyboard(selected))

@router.callback_query(F.data == "select_types")
async def cb_select_types(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user_data = await get_user_data(callback.from_user.id)
    if not user_data or not user_data.get('session_id'):
        await callback.message.answer("❌ يرجى تعيين الجلسة أولاً")
        return
    if not user_data.get('target_id'):
        await callback.message.answer("❌ يرجى تعيين الهدف أولاً")
        return
    selected = user_data.get('report_types', '').split(',') if user_data.get('report_types') else []
    await state.update_data(selected_types=selected)
    await state.set_state(ReportState.selecting_types)
    await callback.message.answer("اختر أنواع البلاغات (اضغط على النوع لتحديده، ثم Done عند الانتهاء):", 
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

@router.callback_query(F.data == "random_types")
async def cb_random_types(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    current_selected = data.get("selected_types", [])
    await state.update_data(previous_selected=current_selected)
    await state.set_state(ReportState.waiting_for_random_count)
    await callback.message.answer(
        f"🎲 أرسل عدد الأنواع التي تريد اختيارها عشوائياً (1 إلى {len(ALL_TYPES)}):\n"
        "مثال: 5"
    )

@router.message(ReportState.waiting_for_random_count)
async def receive_random_count(message: Message, state: FSMContext):
    try:
        count = int(message.text.strip())
        max_count = len(ALL_TYPES)
        if count < 1 or count > max_count:
            await message.answer(f"❌ الرقم يجب أن يكون بين 1 و {max_count}. حاول مرة أخرى.")
            return
        selected_keys = random.sample(ALL_TYPES, count)
        await state.update_data(selected_types=selected_keys)
        await state.set_state(ReportState.selecting_types)
        await message.answer(
            "✅ تم اختيار الأنواع عشوائياً. يمكنك تعديلها ثم الضغط على Done:",
            reply_markup=get_report_types_keyboard(selected_keys)
        )
    except ValueError:
        await message.answer("❌ يرجى إرسال رقم صحيح.")

@router.callback_query(F.data == "types_done")
async def cb_types_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected_types", [])
    if not selected:
        await callback.answer("لم تختر أي نوع!", show_alert=True)
        return
    selected_str = ",".join(selected)
    await save_report_types(callback.from_user.id, selected_str)
    await callback.message.edit_text(f"✅ تم حفظ {len(selected)} نوع من البلاغات.")
    await state.set_state(None)
    await _send_report_confirmation(callback.message, callback.from_user.id)

async def _send_report_confirmation(target, user_id: int):
    user_data = await get_user_data(user_id)
    if not user_data or not user_data.get('session_id'):
        await target.answer("❌ لا توجد جلسة. استخدم /set_session")
        return
    if not user_data.get('target_id'):
        await target.answer("❌ لم يتم تعيين هدف. استخدم /set_target")
        return
    if not user_data.get('report_types'):
        await target.answer("❌ لم تختر أي نوع بلاغ. استخدم /select_types")
        return
    report_keys = user_data['report_types'].split(',')
    target_username = user_data['target_username']
    confirm_text = (f"⚠️ <b>تأكيد الإبلاغ</b>\n\n"
                    f"الهدف: @{target_username}\n"
                    f"عدد أنواع البلاغات: {len(report_keys)}\n"
                    f"<b>إجمالي البلاغات المرسلة: {len(report_keys)}</b>\n\n"
                    f"هل تريد المتابعة؟")
    await target.answer(confirm_text, reply_markup=get_confirmation_keyboard())

@router.callback_query(F.data == "confirm_yes")
async def cb_confirm_yes(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id
    user_data = await get_user_data(user_id)
    if not user_data:
        await callback.message.edit_text("❌ البيانات ناقصة. ابدأ من جديد بـ /start")
        return
    report_keys = user_data['report_types'].split(',')
    session_id = user_data['session_id']
    target_id = user_data['target_id']
    target_username = user_data.get('target_username', 'Unknown')
    
    total = len(report_keys)
    progress_msg = await callback.message.edit_text(f"🔄 جاري إرسال البلاغات...\n0/{total} تم")
    
    start_time = asyncio.get_event_loop().time()
    success_total = 0
    failed_total = 0
    current_total = 0
    
    for idx, key in enumerate(report_keys, 1):
        report_type = REPORT_TYPES[key]
        success = await report_service.report(target_id, session_id, report_type)
        if success:
            success_total += 1
        else:
            failed_total += 1
        current_total += 1
        status = "✅" if success else "❌"
        text = f"🔄 التقدم: {current_total}/{total}\nآخر بلاغ: {status} {report_type['name']}"
        try:
            await progress_msg.edit_text(text)
        except Exception:
            pass
        await log_report(user_id, report_type['name'], success)
        await asyncio.sleep(random.uniform(10, 20))
    
    end_time = asyncio.get_event_loop().time()
    elapsed = end_time - start_time
    
    first_type_name = REPORT_TYPES.get(report_keys[0], {}).get('name', 'بلاغ') if report_keys else 'بلاغ'
    
    final_text = (
        "╭━━━━━━━━━━━━━━━━━━━━╮\n"
        "      تم الانتهاء من البلاغات\n"
        "╰━━━━━━━━━━━━━━━━━━━━╯\n"
        f"📋 💢 {first_type_name}\n"
        f"🎯 {target_username}\n"
        f"✅ {success_total} | ❌ {failed_total}\n"
        f"⏱ {elapsed:.1f}s"
    )
    await progress_msg.edit_text(final_text)
    await callback.message.answer("القائمة الرئيسية:", reply_markup=get_main_keyboard())
    await state.clear()

@router.callback_query(F.data == "confirm_no")
async def cb_confirm_no(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text("❌ تم إلغاء الإبلاغ.")
    await callback.message.answer("القائمة الرئيسية:", reply_markup=get_main_keyboard())
    await state.clear()

@router.callback_query(F.data == "my_data")
async def cb_my_data(callback: CallbackQuery):
    await callback.answer()
    user_data = await get_user_data(callback.from_user.id)
    if not user_data:
        text = "لا توجد بيانات. استخدم /start للإعداد."
    else:
        text = f"📊 <b>بياناتك</b>\n"
        text += f"الجلسة: {'✅' if user_data.get('session_id') else '❌'}\n"
        text += f"اسم المستخدم: @{user_data.get('username') or 'غير معرف'}\n"
        text += f"الهدف: @{user_data.get('target_username') or 'غير محدد'}\n"
        text += f"أنواع البلاغات: {len(user_data.get('report_types', '').split(',')) if user_data.get('report_types') else 0}\n"
    await callback.message.answer(text, reply_markup=get_main_keyboard())
