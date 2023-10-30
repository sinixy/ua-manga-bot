from aiogram import Bot, Router, types, F

from bot.utils import ts_to_strdt, notify_admins
from bot.keyboards.user import user_menu
from bot.models import User, Team
from bot.models.enums import ReminderType
from bot.jobs.reminder import set_minor_reminder, set_major_reminder, set_confirmation_reminder


reminder_router = Router(name=__name__)


async def reschedule_reminder(type: ReminderType, user_id: int):
    match type:
        case ReminderType.MINOR:
            return await set_minor_reminder(user_id)
        case ReminderType.MAJOR:
            return await set_major_reminder(user_id)
        case _:
            return None

async def notify_admins_about_confirmation(choice: str, reminder_type: ReminderType, user: User, team: Team, bot: Bot):
    user_chat = await bot.get_chat(user.id)
    reminder_type_str = ReminderType.to_ukr(reminder_type)

    if choice == "yes":
        text = f"👍 Користувач @{user_chat.username} з команди <b>{team.name}</b> " \
        f"підтвердив, що надіслав <b>{reminder_type_str}</b> оновлення адмінам."
    else:
        text = f"👎 Користувач @{user_chat.username} з команди <b>{team.name}</b> " \
               f"передумав робити <b>{reminder_type_str}</b> оновлення."
    await notify_admins(bot, text)

@reminder_router.callback_query(F.data == "enrem")
async def enable_reminders(callback: types.CallbackQuery, user: User):
    await callback.message.delete_reply_markup()

    if await user.get_reminders():
        await callback.message.edit_text("⚠️ <b>У вас уже виставлені нагадування!</b> \n\nЯкщо це помилка – повідомте адмінам.")
        return

    minor_reminder = await set_minor_reminder(user.id)
    major_reminder = await set_major_reminder(user.id)

    await callback.message.answer(
        f"⏰ Нагадування для звичайного оновлення прийде {ts_to_strdt(minor_reminder.remind_at)}, " \
        f"а для повного – {ts_to_strdt(major_reminder.remind_at)}! \n\nУ меню знизу можеш перевірити свої нагадування, " \
        "а також змінити назву команди чи видалити її 👇",
        reply_markup=user_menu
    )
    await callback.message.delete()

@reminder_router.callback_query(F.data.startswith("update:yes"))
async def handle_agree_update(callback: types.CallbackQuery, bot: Bot, user: User, team: Team):
    await callback.message.edit_text(text=callback.message.text + "\n\n✅ <b>Надішлемо новий пост</b>")

    reminder_type = callback.data.split(":")[-1]
    confirmation_reminder = await set_confirmation_reminder(user.id, ReminderType[reminder_type])

    await callback.message.reply(f"Чудово, {ts_to_strdt(confirmation_reminder.remind_at)} буде додаткове нагадування, щоб підтвердити, що пост надіслано :)")

    await notify_admins(
        bot,
        f"🙋‍♀️ Користувач @{callback.from_user.username} з команди {team.name} вирішив робити <b>{ReminderType.to_ukr(reminder_type)}</b> оновлення. Чекаємо підтвердження."
    )

@reminder_router.callback_query(F.data.startswith("update:no"))
async def handle_deny_update(callback: types.CallbackQuery, bot: Bot, user: User, team: Team):
    await callback.message.edit_text(text=callback.message.text + "\n\n⛔ <b>Не будемо оновлювати</b>")

    reminder_type = ReminderType[callback.data.split(":")[-1]]
    new_reminder = await reschedule_reminder(reminder_type, user.id)

    await callback.message.reply(f"Добре, наступне оновлення – {ts_to_strdt(new_reminder.remind_at)}!")

    await notify_admins(
        bot,
        f"🙅‍♀️ Користувач @{callback.from_user.username} з команди {team.name} не буде робити <b>{ReminderType.to_ukr(reminder_type)}</b> оновлення."
    )

@reminder_router.callback_query(F.data.startswith("confirmupd"))
async def handle_update_confirmation(callback: types.CallbackQuery, bot: Bot, user: User, team: Team):
    _, choice, reminder_type = callback.data.split(":")
    if choice == "yes":
        new_text = callback.message.text + "\n\n✅ <b>Надіслали</b>"
    else:
        new_text = callback.message.text + "\n\n⛔ <b>Передумали</b>"
    await callback.message.edit_text(text=new_text)

    reminder_type = ReminderType[reminder_type]
    new_reminder = await reschedule_reminder(reminder_type, user.id)

    await callback.message.reply(f"Добре, наступне оновлення – {ts_to_strdt(new_reminder.remind_at)}!")
    await notify_admins_about_confirmation(choice, reminder_type, user, team, bot)