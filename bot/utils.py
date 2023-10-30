from aiogram import Bot, types
from datetime import datetime

from bot.models import User, Team


def ts_to_dt(ts: float) -> datetime:
    return datetime.fromtimestamp(ts)

def ts_to_strdt(ts: float) -> str:
    return ts_to_dt(ts).strftime('%H:%M %d-%m-%Y')

def chat_to_str(chat: types.Chat) -> str:
    return f"@{chat.username} [uid=<code>{chat.id}</code>]"

async def notify_admins(bot: Bot, text: str, reply_markup: types.InlineKeyboardMarkup = None):
    for admin in await User.find_admins():
        try:
            await bot.send_message(
                chat_id=admin.id,
                text=text,
                reply_markup=reply_markup
            )
        except Exception:
            continue

async def notify_user(bot: Bot, chat_id: int, text: str):
    try:
        await bot.send_message(chat_id, text)
    except:
        return

async def delete_team(id: int, bot: Bot, reason: str = ""):
    user = await User.get(id)
    for reminder in await user.get_reminders():
        await reminder.delete(with_job=True)

    team = await Team.get(id)
    await team.delete()
    await notify_admins(bot, f"🫡 Команду <b>{team.name}</b> було видалено: {reason}")
