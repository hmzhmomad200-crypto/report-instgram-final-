import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers import start, session, target, report, admin
from middlewares.antiflood import AntiFloodMiddleware
from middlewares.auth import AuthMiddleware
from utils.logger import logger
from database.db import init_db

async def on_startup():
    await init_db()
    logger.info("Bot started")

async def on_shutdown():
    logger.info("Bot shutting down")

def create_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    dp.message.middleware(AntiFloodMiddleware())
    dp.callback_query.middleware(AntiFloodMiddleware())
    dp.message.middleware(AuthMiddleware())
    
    dp.include_router(start.router)
    dp.include_router(session.router)
    dp.include_router(target.router)
    dp.include_router(report.router)
    dp.include_router(admin.router)
    
    return dp

async def start_bot():
    bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
    dp = create_dispatcher()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

def main():
    asyncio.run(start_bot())

if __name__ == "__main__":
    main()