from aiogram import Router

from .approval import approval_router
from .menu import menu_router
from bot.middlewares import AdminMiddleware


admin_router = Router(name=__name__)

admin_router.message.middleware(AdminMiddleware())
admin_router.callback_query.middleware(AdminMiddleware())

admin_router.include_router(approval_router)
admin_router.include_router(menu_router)