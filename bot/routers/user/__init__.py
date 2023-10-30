from aiogram import Router

from .signup import signup_router
from .reminder import reminder_router
from .menu import menu_router

from bot.middlewares import UserReminderMiddleware, UserMenuMiddleware


user_router = Router(name=__name__)

reminder_router.callback_query.middleware(UserReminderMiddleware())
menu_router.message.middleware(UserMenuMiddleware())

user_router.include_router(signup_router)
user_router.include_router(reminder_router)
user_router.include_router(menu_router)