from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from bot.config import Config
from bot.routers import user_router, admin_router
from bot.middlewares import GlobalMiddleware


bot = Bot(Config.BOT_TOKEN, parse_mode=ParseMode.HTML)

dp = Dispatcher()

dp.message.middleware(GlobalMiddleware())
dp.callback_query.middleware(GlobalMiddleware())

dp.include_router(user_router)
dp.include_router(admin_router)
