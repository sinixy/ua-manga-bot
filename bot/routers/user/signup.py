from aiogram import Bot, Router, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from bot.config import Config
from bot.utils import notify_admins, chat_to_str
from bot.keyboards.user import team_name_confirmation_kb, user_menu
from bot.keyboards.admin import admin_menu
from bot.keyboards.common import request_approval_kb
from bot.models import User, Team, Request
from bot.models.enums import Role


signup_router = Router(name=__name__)

class Form(StatesGroup):
    team_name = State()
    team_name_confirmation = State()


async def send_approval_request_to_admins(bot: Bot, request: Request):
    sender_chat = await bot.get_chat(request.sender)
    text = f"❗️ <b>Новий запит на реєстрацію команди</b> \n\n" \
    f"Команда: {request.team_name}\n" \
    f"Користувач: {chat_to_str(sender_chat)}"
    reply_markup = request_approval_kb(str(request.id))
    await notify_admins(bot, text, reply_markup)
    

@signup_router.message(CommandStart())
async def start(message: types.Message, state: FSMContext, user: User):
    if user:
        if user.role == Role.ADMIN:
            await message.answer("Welcome home, onee-chan QwQ", reply_markup=admin_menu)
            await state.clear()
            return
        
        team = await user.get_team()
        requests = await user.find_requests()
        if team:
            await message.answer(
                f"Привіт ще раз! За тобою вже закріплена команда <b>{team.name}</b>. "
                "Якщо хочеш створити нову команду, то спочатку видали стару через меню та перезапусти бота.",
                reply_markup=user_menu
            )
            await state.clear()
        elif requests:
            await message.answer(f"Привіт ще раз! Твій запит на реєстрацію команди <b>{requests[0].team_name}</b> в процесі обробки. Почекай трішки або напиши адмінці.")
        else:
            await message.answer("Привіт ще раз! Цей бот буде тобі нагадувати про оновлення постів кожних 3 та 6 місяців (звичайне та повне оновлення). Щоб почати роботу, введи назву команди:")
            await state.set_state(Form.team_name)
    else:
        await User.create(message.from_user.id)
        await state.set_state(Form.team_name)
        await message.answer(f"Привіт! Цей бот буде тобі нагадувати про оновлення постів кожних 3 та 6 місяців (звичайне та повне оновлення, детальніше за посиланням https://t.me/UA_manga_extra/30). Щоб почати роботу, введи назву команди:")

@signup_router.message(Command("menu"))
async def enable_menu(message: types.Message, user: User):
    match user.role:
        case Role.USER:
            team = await user.get_team()
            if team:
                await message.answer("<b>Меню</b>", reply_markup=user_menu)
            else:
                await message.answer("Спочатку створи команду!") 
        case Role.ADMIN:
            await message.answer("<b>Меню адміна</b>", reply_markup=admin_menu)

@signup_router.message(Form.team_name, F.text)
async def process_team_name(message: types.Message, state: FSMContext):
    team_name = message.text
    if len(team_name) > Config.MAX_TEAM_NAME_LENGTH:
        await message.answer("На жаль, назва команди занадто довга :(\n\nСпробуй ще раз:")
        return
    
    team = await Team.get(name=team_name)
    if team:
        await message.answer(f"На жаль, команда з назвою <b>{team_name}</b> вже існує. Спробуй іншу назву або звернися до адмінки.")
        return

    await state.set_state(Form.team_name_confirmation)
    await state.update_data(team_name=team_name)
    await message.answer(
        f"Супер! Надіслати запит на реєстрацію команди <b>{team_name}</b>?",
        reply_markup=team_name_confirmation_kb
    )

@signup_router.message(Form.team_name)
async def process_invalid_team_name(message: types.Message):
    await message.answer("Некоректний тип повідомлення. Спробуй ще раз. Можна тільки текстом :)")

@signup_router.callback_query(Form.team_name_confirmation, F.data == "send")
async def send_for_approval(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    data = await state.get_data()
    team_name = data["team_name"]
    request = await Request.create(callback.from_user.id, team_name)
    await send_approval_request_to_admins(bot, request)

    await callback.message.edit_text(f"Чудово! Запит на створення команди <b>{team_name}</b> надіслано адмінам! Я повідомлю тебе, коли все підтвердять, після чого ти зможеш отримувати нагадування.")

    await state.clear()

@signup_router.callback_query(Form.team_name_confirmation, F.data == "edit")
async def edit_team_name(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Form.team_name)
    await callback.message.edit_text("Введи назву ще раз:")
