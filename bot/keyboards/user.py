from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from bot.models.enums import ReminderType


team_name_confirmation_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Надіслати", callback_data="send")],
    [InlineKeyboardButton(text="Виправити назву", callback_data="edit")]
])

user_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Команда")],
    [KeyboardButton(text="Нагадування")]
], resize_keyboard=True)

user_team_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Змінити назву")],
    [KeyboardButton(text="Видалити")],
    [KeyboardButton(text="Назад")]
])

def update_reminder_kb(reminder_type: ReminderType):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Надішлемо новий пост", callback_data=f"update:yes:{reminder_type.name}")],
        [InlineKeyboardButton(text="Не будемо оновлювати", callback_data=f"update:no:{reminder_type.name}")]
    ])

def confirm_update_reminder_kb(confirmation_type: ReminderType):
    if confirmation_type == ReminderType.CONFIRM_MINOR:
        target_reminder_type_name = ReminderType.MINOR.name
    else:
        target_reminder_type_name = ReminderType.MAJOR.name
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Надіслали", callback_data=f"confirmupd:yes:{target_reminder_type_name}")],
        [InlineKeyboardButton(text="Передумали", callback_data=f"confirmupd:no:{target_reminder_type_name}")]
    ])
