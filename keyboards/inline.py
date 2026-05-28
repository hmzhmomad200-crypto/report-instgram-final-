from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.instagram_reporter import REPORT_TYPES

def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Set Session ID", callback_data="set_session")],
        [InlineKeyboardButton(text="🎯 Set Target", callback_data="set_target")],
        [InlineKeyboardButton(text="📋 Select Report Types", callback_data="select_types")],
        [InlineKeyboardButton(text="🚀 Start Reporting", callback_data="start_report")],
        [InlineKeyboardButton(text="ℹ️ My Data", callback_data="my_data")],
    ])

def get_report_types_keyboard(selected: list = None):
    keyboard = []
    for key, value in REPORT_TYPES.items():
        text = f"{'✅ ' if selected and key in selected else ''}{key}. {value['name'][:40]}"
        callback = f"toggle_type:{key}"
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
    keyboard.append([InlineKeyboardButton(text="✅ Done", callback_data="types_done")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_confirmation_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Confirm", callback_data="confirm_yes")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="confirm_no")],
    ])