from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


confirmation_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Так", callback_data="confirm")],
    [InlineKeyboardButton(text="Назад", callback_data="back")]
])

cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Відмінити", callback_data="cancel")]
])

set_reminders_kb = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="Поставити нагадування", callback_data="enrem")]]
)

def request_approval_kb(request_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Прийняти", callback_data=f"request:approve:{request_id}")],
        [InlineKeyboardButton(text="Відхилити", callback_data=f"request:decline:{request_id}")]
    ])

