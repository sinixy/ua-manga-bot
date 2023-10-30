from aiogram import Bot, Router, types, F
from aiogram.filters import or_f
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from datetime import datetime

from bot.config import Config
from bot.keyboards.admin import team_list_kb, team_info_kb, team_reminders_kb, admin_menu, admin_users_menu
from bot.keyboards.common import confirmation_kb, cancel_kb
from bot.utils import ts_to_strdt, chat_to_str, delete_team, notify_user
from bot.models import User, Team, Reminder
from bot.models.enums import ReminderType, Role


menu_router = Router(name=__name__)

class TeamsMenu(StatesGroup):
    listing = State()
    info = State()
    confirm_deletion = State()

class RemindersMenu(StatesGroup):
    listing = State()
    reschedule = State()

class UsersMenu(StatesGroup):
    show = State()
    input_ban = State()
    input_unban = State()
    confirm_ban = State()
    confirm_unban = State()


@menu_router.message(RemindersMenu.reschedule, F.text)
async def set_new_time(message: types.Message, state: FSMContext):
    try:
        dt = datetime.strptime(message.text, "%H:%M %d-%m-%Y")
    except:
        await message.answer("Помилка! Спробуй ще раз:", reply_markup=cancel_kb)
        return
    
    data = await state.get_data()
    reminder = data["reminder"]
    await reminder.reschedule(dt)

    reminders = await data["owner"].get_reminders()
    team = data["team"]
    text = f"Нагадування для команди <b>{team.name}</b> \n\n"
    for r in reminders:
        text += f"{ReminderType.to_ukr(r.type).upper()} – {ts_to_strdt(r.remind_at)}\n"

    await message.answer(text, reply_markup=team_reminders_kb(reminders))
    await state.set_state(RemindersMenu.listing)

@menu_router.callback_query(RemindersMenu.listing, F.data.startswith("reminder:"))
async def input_new_time(callback: types.CallbackQuery, state: FSMContext):
    reminder_id = callback.data.split(":")[-1]
    reminder = await Reminder.get(reminder_id)
    if not reminder:
        await callback.answer("⚠️ Цього нагадування більше не існує!")
        return
    
    await state.set_state(RemindersMenu.reschedule)
    await state.update_data(reminder=reminder)

    await callback.message.edit_text(
        "Введіть новий час у форматі ГГ:ХХ ДД-ММ-РРРР (напр 15:07 15-01-2024)",
        reply_markup=cancel_kb
    )

@menu_router.callback_query(RemindersMenu.reschedule, F.data == "cancel")
@menu_router.callback_query(TeamsMenu.info, F.data == "reminders")
async def list_reminders(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(RemindersMenu.listing)
    data = await state.get_data()

    team = data["team"]
    owner = data["owner"]
    reminders = await owner.get_reminders()

    text = f"Нагадування для команди <b>{team.name}</b> \n\n"
    for r in reminders:
        text += f"{ReminderType.to_ukr(r.type).upper()} – {ts_to_strdt(r.remind_at)}\n"

    await callback.message.edit_text(text, reply_markup=team_reminders_kb(reminders))

@menu_router.callback_query(TeamsMenu.confirm_deletion, F.data == "confirm")
async def confirm_team_deletion(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    await callback.message.delete()
    await state.set_state(TeamsMenu.listing)

    data = await state.get_data()
    team = data["team"]
    await delete_team(team.id, bot, reason=f"адмін @{callback.from_user.username} вирішив видалити команду")
    await notify_user(bot, team.id, "❗️ <b>Вашу команду було видалено адміном!</b>")

    page = data.get("page", 0)
    teams = await Team.find(page=page)
    total_count = await Team.get_count()
    await callback.message.answer(
        f"Загальна кількість команд: {total_count} \n\nВиберіть команду, щоб перейти до її редагування.",
        reply_markup=team_list_kb(teams, total_count, page=page)
    )

@menu_router.callback_query(or_f(TeamsMenu.confirm_deletion, RemindersMenu.listing), F.data == "back")
async def back_to_team_info(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    await state.set_state(TeamsMenu.info)
    data = await state.get_data()
    team = data["team"]
    owner_chat = await bot.get_chat(team.id)
    await callback.message.edit_text(
        f"Команда <b>{team.name}</b> \n\nВласник: {chat_to_str(owner_chat)} \nСтворено: {ts_to_strdt(team.created_at)}",
        reply_markup=team_info_kb
    )

@menu_router.callback_query(TeamsMenu.info, F.data == "delete")
async def handle_delete_team(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(TeamsMenu.confirm_deletion)
    await callback.message.edit_text(f"Видалити команду <b>{data['team'].name}</b>?", reply_markup=confirmation_kb)

@menu_router.callback_query(TeamsMenu.info, F.data == "back")
async def back_to_teams_list(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(team=None, owner=None)
    await state.set_state(TeamsMenu.listing)

    data = await state.get_data()
    page = data.get("page", 0)
    teams = await Team.find(page=page)
    total_count = await Team.get_count()

    await callback.message.edit_text(
        f"Загальна кількість команд: {total_count} \n\nВиберіть команду, щоб перейти до її редагування.",
        reply_markup=team_list_kb(teams, total_count, page=page)
    )

@menu_router.callback_query(TeamsMenu.listing, F.data.startswith("team:"))
async def select_team(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    team_id = int(callback.data.split(":")[-1])
    team = await Team.get(team_id)
    owner = await team.get_owner()
    owner_chat = await bot.get_chat(owner.id)

    await state.update_data(team=team, owner=owner)
    await state.set_state(TeamsMenu.info)

    await callback.message.edit_text(
        f"Команда <b>{team.name}</b> \n\nВласник: {chat_to_str(owner_chat)} \nСтворено: {ts_to_strdt(team.created_at)}",
        reply_markup=team_info_kb
    )

@menu_router.callback_query(TeamsMenu.listing, (F.data == "next") | (F.data == "prev"))
async def teams_list_change_page(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    delta = 1
    if callback.data == "prev":
        delta = -1 
    page = data["page"] + delta

    teams = await Team.find(page=page, count=Config.ITEMS_PER_PAGE)
    total_count = await Team.get_count()

    await callback.message.edit_text(
        f"Загальна кількість команд: {total_count} \n\nВиберіть команду, щоб перейти до її редагування.",
        reply_markup=team_list_kb(teams, total_count, page=page)
    )
    await state.update_data(page=page)

@menu_router.callback_query(TeamsMenu.listing, F.data == "exit")
async def filter_list_quit(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.set_state(None)

@menu_router.message(F.text.lower() == "команди")
async def list_teams(message: types.Message, bot: Bot, state: FSMContext):
    await state.set_state(TeamsMenu.listing)
    await state.update_data(page=0)

    teams = await Team.find(page=0)
    total_count = await Team.get_count()

    await message.answer(
        f"Загальна кількість команд: {total_count} \n\nВиберіть команду, щоб перейти до її редагування.",
        reply_markup=team_list_kb(teams, total_count, page=0)
    )


# ======== USERS ========
# TO-DO: refactor this copypaste bs
async def validate_uid(uid: str, bot: Bot) -> types.Chat | None:
    try:
        chat = await bot.get_chat(int(uid))
    except:
        return None
    if not await User.get(int(uid)):
        return None
    return chat

@menu_router.callback_query(UsersMenu.confirm_ban, F.data == "confirm")
async def punish_mortal(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    await callback.message.delete()

    data = await state.get_data()
    target_user = data["target_user"]
    if target_user.role == Role.ADMIN:
        await callback.message.answer(f"Адмінів блокувати не можна! Зверніться до розробника.")
        await state.set_state(UsersMenu.show)
        return
    
    await target_user.ban()

    await callback.message.answer(f"Користувача uid={target_user.id} було заблоковано!")
    await state.set_state(UsersMenu.show)

    team = await target_user.get_team()
    if team:
        await delete_team(target_user.id, bot, f"власника uid={target_user.id} було заблоковано")

@menu_router.callback_query(UsersMenu.confirm_unban, F.data == "confirm")
async def excuse_mortal(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()

    data = await state.get_data()
    target_user = data["target_user"]
    await target_user.unban()

    await callback.message.answer(f"Користувач uid={target_user.id} був розблокований!")
    await state.set_state(UsersMenu.show)

@menu_router.message(UsersMenu.input_ban)
async def confirm_ban(message: types.Message, bot: Bot, state: FSMContext):
    uid = message.text
    user_chat = await validate_uid(uid, bot)
    if not user_chat:
        await message.answer("Не вдалося знайти користувача. Спробуйте ще раз:", reply_markup=cancel_kb)
        return

    await message.answer(f"Заблокувати користувача {chat_to_str(user_chat)}?", reply_markup=confirmation_kb)
    await state.update_data(target_user = await User.get(int(uid)))
    await state.set_state(UsersMenu.confirm_ban)

@menu_router.message(UsersMenu.input_unban)
async def confirm_unban(message: types.Message, bot: Bot, state: FSMContext):
    uid = message.text
    user_chat = await validate_uid(uid, bot)
    if not user_chat:
        await message.answer("Не вдалося знайти користувача. Спробуйте ще раз:", reply_markup=cancel_kb)
        return

    await message.answer(f"Розблокувати користувача {chat_to_str(user_chat)}?", reply_markup=confirmation_kb)
    await state.update_data(target_user = await User.get(int(uid)))
    await state.set_state(UsersMenu.confirm_unban)

@menu_router.callback_query(or_f(UsersMenu.confirm_ban, UsersMenu.confirm_unban), F.data == "back")
@menu_router.callback_query(or_f(UsersMenu.input_ban, UsersMenu.input_unban), F.data == "cancel")
async def back_to_users_menu(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.set_state(UsersMenu.show)

@menu_router.message(UsersMenu.show, (F.text.lower() == "заблокувати") | (F.text.lower() == "розблокувати"))
async def input_uid(message: types.Message, state: FSMContext):
    await message.answer("Введіть user id (uid) користувача:", reply_markup=cancel_kb)
    if message.text.lower() == "заблокувати":
        await state.set_state(UsersMenu.input_ban)
    else:
        await state.set_state(UsersMenu.input_unban)

@menu_router.message(UsersMenu.show, F.text.lower() == "назад")
async def back_to_admin_menu(message: types.Message, state: FSMContext):
    await state.set_state(None)
    await message.answer("<b>Головне меню</b>", reply_markup=admin_menu)

@menu_router.message(F.text.lower() == "користувачі")
async def show_users_menu(message: types.Message, bot: Bot, state: FSMContext):
    await state.set_state(UsersMenu.show)
    await message.answer(f"Меню користувачів", reply_markup=admin_users_menu)