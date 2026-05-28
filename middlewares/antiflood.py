from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from collections import defaultdict
import time
from config import RATE_LIMIT_PER_MINUTE

class AntiFloodMiddleware(BaseMiddleware):
    def __init__(self):
        self.user_requests = defaultdict(list)
    
    async def __call__(self, handler, event, data):
        user_id = None
        if isinstance(event, (Message, CallbackQuery)):
            user_id = event.from_user.id
        if user_id:
            now = time.time()
            window_start = now - 60
            self.user_requests[user_id] = [t for t in self.user_requests[user_id] if t > window_start]
            if len(self.user_requests[user_id]) >= RATE_LIMIT_PER_MINUTE:
                if isinstance(event, Message):
                    await event.answer("⏳ Too many requests! Please wait a moment.")
                elif isinstance(event, CallbackQuery):
                    await event.answer("⏳ Too many requests! Slow down.", show_alert=True)
                return
            self.user_requests[user_id].append(now)
        return await handler(event, data)