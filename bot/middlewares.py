from aiogram import BaseMiddleware, types
from aiogram.types import TelegramObject
from typing import Callable, Dict, Any, Awaitable, Union

from bot.models import User
from bot.models.enums import Role


class GlobalMiddleware(BaseMiddleware):

    async def __call__(self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Union[types.Message, types.CallbackQuery],
        data: Dict[str, Any]
    ):
        data["user"] = await User.get(event.from_user.id)
        if data["user"]:
            if data["user"].banned:
                return
        else:
            if isinstance(event, types.Message):
                if event.text != "/start":
                    await event.answer("Будь ласка, напишіть /start, щоб зареєструватися в боті.")
                    return
            else:
                await data["bot"].send_message(event.from_user.id, "Будь ласка, напишіть /start, щоб зареєструватися в боті.")
                return
        
        return await handler(event, data)


class AdminMiddleware(BaseMiddleware):
    async def __call__(self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Union[types.Message, types.CallbackQuery],
        data: Dict[str, Any]
    ):
        if data["user"].role != Role.ADMIN:
            return
        
        return await handler(event, data)

class UserReminderMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
        event: types.CallbackQuery,
        data: Dict[str, Any]
    ):
        user = data["user"]
        team = await user.get_team()
        if not team:
            # this might occure when the user received a reminder and pressed on its button after deleting they own team
            await event.message.delete()
            return

        data["team"] = team

        return await handler(event, data)
    

class UserMenuMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
        event: types.Message,
        data: Dict[str, Any]
    ):
        user = data["user"]
        team = await user.get_team()
        if not team:
            return

        data["team"] = team
        
        return await handler(event, data)