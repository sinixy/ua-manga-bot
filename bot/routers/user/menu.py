from aiogram import Bot, Router, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from bot.config import Config
from bot.keyboards.user import user_menu, user_team_menu
from bot.keyboards.common import confirmation_kb, cancel_kb
from bot.utils import ts_to_strdt, chat_to_str, delete_team, notify_admins
from bot.models import User, Team
from bot.models.enums import ReminderType


menu_router = Router(name=__name__)

class TeamMenu(StatesGroup):
    selected = State()
    team_name = State()
    confirm_deletion = State()


@menu_router.message(TeamMenu.selected)
async def handle_team_action(message: types.Message, state: FSMContext):
    match message.text.lower():
        case "змінити назву":
            await message.answer("Введи нову назву команди:", reply_markup=cancel_kb)
            await state.set_state(TeamMenu.team_name)
        case "видалити":
            await message.answer("Видалити команду?", reply_markup=confirmation_kb)
            await state.set_state(TeamMenu.confirm_deletion)
        case "назад":
            await message.answer("<b>Головне меню</b>", reply_markup=user_menu)
            await state.set_state(None)
        case _:
            await message.answer("Шо?")

@menu_router.message(TeamMenu.team_name)
async def process_team_name(message: types.Message, state: FSMContext, bot: Bot, team: Team):
    team_name = message.text
    if len(team_name) > Config.MAX_TEAM_NAME_LENGTH:
        await message.answer("Вибач, але назва команди занадто довга :(\n\nСпробуй ще раз:")
        return
    existing_team = await Team.get(name=team_name)
    if existing_team:
        await message.answer(f"Вибач, але команда з назвою <b>{team_name}</b> вже існує :(\n\nСпробуй іншу назву або звернися до адмінів.")
        return
    
    old_team_name = team.name
    await team.change_name(team_name)

    await state.set_state(None)
    await message.answer(f"Назву команди успішно змінено на <b>{team_name}</b>!", reply_markup=user_menu)
    await notify_admins(bot, f"🔄 Команда <b>{old_team_name}</b> (@{message.from_user.username}) змінила назву на <b>{team_name}</b>!")

@menu_router.callback_query(TeamMenu.confirm_deletion, F.data == "back")
@menu_router.callback_query(TeamMenu.team_name, F.data == "cancel")
async def cancel_team_name_input(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("<b>Меню команди</b>", reply_markup=user_team_menu)
    await callback.message.delete()
    await state.set_state(TeamMenu.selected)

@menu_router.callback_query(TeamMenu.confirm_deletion, F.data == "confirm")
async def confirm_team_deletion(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    user_chat = callback.from_user
    await delete_team(user_chat.id, bot, f"користувач {chat_to_str(user_chat)} вирішив видалити команду")
    await callback.message.answer(
        "<b>Команду успішно видалено!</b> \n\nВведіть /start, щоб почати знову.",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await callback.message.delete()
    await state.clear()


@menu_router.message(F.text.lower() == "команда")
async def open_team_menu(message: types.Message, state: FSMContext, team: Team):
    await message.answer(f"Ваша зареєстрована команда – {team.name}", reply_markup=user_team_menu)
    await state.set_state(TeamMenu.selected)

@menu_router.message(F.text.lower() == "нагадування")
async def show_reminders(message: types.Message, user: User):
    reminders = await user.get_reminders()

    text = ""
    for r in reminders:
        text += f"<b>{ReminderType.to_ukr(r.type).capitalize()}</b> оновлення: {ts_to_strdt(r.remind_at)}\n"

    if not text:
        text = "Нагадування відсутні!"
    await message.answer(text)
