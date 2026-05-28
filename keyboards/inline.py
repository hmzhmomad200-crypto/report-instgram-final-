from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.instagram_reporter import REPORT_TYPES

def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 تعيين جلسة", callback_data="set_session")],
        [InlineKeyboardButton(text="🎯 تعيين هدف", callback_data="set_target")],
        [InlineKeyboardButton(text="📋 اختيار أنواع البلاغات", callback_data="select_types")],
        [InlineKeyboardButton(text="ℹ️ بياناتي", callback_data="my_data")],
    ])

def get_report_types_keyboard(selected: list = None):
    keyboard = []
    # عرض جميع الأنواع الموجودة في REPORT_TYPES (1 إلى 34)
    for key, value in REPORT_TYPES.items():
        text = f"{'✅ ' if selected and key in selected else ''}{key}. {value['name'][:40]}"
        callback = f"toggle_type:{key}"
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
    # إضافة زر Random
    keyboard.append([InlineKeyboardButton(text="🎲 Random", callback_data="random_types")])
    keyboard.append([InlineKeyboardButton(text="✅ تم", callback_data="types_done")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_confirmation_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ تأكيد", callback_data="confirm_yes")],
        [InlineKeyboardButton(text="❌ إلغاء", callback_data="confirm_no")],
    ])
