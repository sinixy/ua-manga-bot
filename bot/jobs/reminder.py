from aiogram import Bot, types
from aiogram.exceptions import TelegramForbiddenError
from datetime import datetime, timedelta

from bot.config import Config
from bot.utils import delete_team, notify_admins
from bot.models import Reminder, Team
from bot.models.enums import ReminderType
from bot.keyboards.user import update_reminder_kb, confirm_update_reminder_kb
from bot.scheduler import scheduler


async def _send_reminder(
          bot: Bot,
          user_id: int,
          reminder_id: str,
          text: str,
          reply_markup: types.InlineKeyboardMarkup):
    reminder = await Reminder.get(reminder_id)
    await reminder.delete()
    
    try:
        await bot.send_message(user_id, text, reply_markup=reply_markup, disable_web_page_preview=True)
    except TelegramForbiddenError:
        await delete_team(user_id, bot, reason="користувач заблокував бота")
    except Exception as e:
        await notify_admins(bot, f"⚠️ Помилка відправки нагадування користувачу ID={user_id}: {e}")
        

async def _set_reminder(user_id: int, type: ReminderType) -> Reminder:
    now = datetime.now()
    reminder_id = f"{type.name}-{user_id}-{int(now.timestamp())}"
    reminder_str = ReminderType.to_ukr(type).upper()

    # TO-DO (maybe): create a class for each type cuz cringe
    match type:
        case ReminderType.MINOR:
            text = f"🌱 <b>{reminder_str} оновлення</b>\n\n" \
            "Привіт, пора оновити пост команди на каналі @UA_manga :) \nПисати адмінці в особисті. \n" \
            "Деталі про написання можна знайти тут: https://t.me/UA_manga_extra/30  \n\n" \
            "Обов'язково натисни одну з кнопок, щоб повідомити мене про своє рішення та поставити нове нагадування 👇"
            reply_markup = update_reminder_kb(reminder_type=type)
            tdelta = Config.MINOR_REMINDER_INTERVAL
        case ReminderType.MAJOR:
            text = f"🌱 <b>{reminder_str} оновлення</b>\n\n" \
            "Привіт, пора повністю оновити пост твоєї команди на каналі @UA_manga :) \nПисати адмінці в особисті. \n" \
            "Деталі про написання можна знайти тут: https://t.me/UA_manga_extra/30  \n\n" \
            "Обов'язково натисни одну з кнопок, щоб повідомити мене про своє рішення та поставити нове нагадування 👇"
            reply_markup = update_reminder_kb(reminder_type=type)
            tdelta = Config.MAJOR_REMINDER_INTERVAL
        case ReminderType.CONFIRM_MINOR | ReminderType.CONFIRM_MAJOR:
            text = f"❗️ <b>{reminder_str} оновлення</b>\n\n" \
            "Привіт, ви вже надіслали новий пост адмінці?\n\n" \
            "Обов'язково натисни одну з кнопок, щоб повідомити мене про своє рішення та поставити нове нагадування 👇"
            reply_markup = confirm_update_reminder_kb(confirmation_type=type)
            tdelta = Config.CONFIRM_REMINDER_INTERVAL
        case _:
            return

    job = scheduler.add_job(
        _send_reminder,
        "date",
        kwargs={"user_id": user_id, "reminder_id": reminder_id, "text": text, "reply_markup": reply_markup},
        run_date=now + tdelta,
        misfire_grace_time=None
    )

    return await Reminder.create(
        id=reminder_id,
        job_id=job.id,
        receiver_id=user_id,
        remind_at=job.trigger.run_date.timestamp(),
        type=type
    )

async def set_minor_reminder(user_id: int) -> Reminder:
    return await _set_reminder(user_id, ReminderType.MINOR)

async def set_major_reminder(user_id: int) -> Reminder:
    return await _set_reminder(user_id, ReminderType.MAJOR)

async def set_confirmation_reminder(user_id: int, target_type: ReminderType) -> Reminder:
    if target_type == ReminderType.MINOR:
        return await _set_reminder(user_id, ReminderType.CONFIRM_MINOR)
    else:
        return await _set_reminder(user_id, ReminderType.CONFIRM_MAJOR)
