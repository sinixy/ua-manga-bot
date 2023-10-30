from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List

from bot.config import Config
from bot.models import Team, Reminder
from bot.models.enums import ReminderType


admin_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Команди")],
    [KeyboardButton(text="Користувачі")]
], resize_keyboard=True)

admin_users_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Заблокувати")],
    [KeyboardButton(text="Розблокувати")],
    [KeyboardButton(text="Назад")]
], resize_keyboard=True)

team_info_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Нагадування", callback_data="reminders")],
    [InlineKeyboardButton(text="Видалити", callback_data="delete")],
    [InlineKeyboardButton(text="Назад", callback_data="back")]
])

def team_list_kb(teams: List[Team], total_count: int, page: int = 0, count: int = Config.ITEMS_PER_PAGE):
    builder = InlineKeyboardBuilder()

    for t in teams:
        builder.row(InlineKeyboardButton(text=t.name, callback_data=f"team:{t.id}"))

    builder.adjust(4)

    if total_count > count:
        control_buttons = []
        if page > 0:
            control_buttons.append(InlineKeyboardButton(text="⬅️", callback_data="prev"))
        start = page * count
        end = start + count
        if end < total_count:
            control_buttons.append(InlineKeyboardButton(text="➡️", callback_data="next"))
        builder.row(*control_buttons)
        
    builder.row(InlineKeyboardButton(text="❌ Вийти", callback_data="exit"))
    return builder.as_markup()

def team_reminders_kb(reminders: List[Reminder]):
    builder = InlineKeyboardBuilder()

    for r in reminders:
        builder.row(
            InlineKeyboardButton(
                text=f"Змінити {ReminderType.to_ukr(r.type)}",
                callback_data=f"reminder:{r.id}"
            )
        )

    builder.row(InlineKeyboardButton(text="Назад", callback_data="back"))
    return builder.as_markup()