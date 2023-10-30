from aiogram import Router, types, F, Bot
from aiogram.exceptions import TelegramForbiddenError
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from datetime import datetime

from bot.models import Team, Request
from bot.models.enums import RequestStatus
from bot.keyboards.common import confirmation_kb, request_approval_kb, set_reminders_kb


approval_router = Router(name=__name__)


class Approval(StatesGroup):
    confirm = State()


async def send_approval_notificaition(request: Request, bot: Bot):
    reply_markup = None

    match request.status:
        case RequestStatus.APPROVED:
            text = f"✅ <b>Вітаю! Твій запит на створення команди {request.team_name} було прийнято!</b>\n\n" \
            "Тисни кнопку, щоб почати отримувати нагадування про оновлення постів 👇"
            reply_markup = set_reminders_kb
        case RequestStatus.DECLINED:
            text = f"⛔️ <b>Вибач, але твій запит на створення команди {request.team_name} було відхилено :(</b>\n\n" \
            "Можеш звернутися до адмінки, щоб дізнатися більше, або натисни /start, щоб зареєструвати іншу команду."
        case _:
            await bot.send_message(request.approval_info["by"], f"⚠️ <b>INVALID REQUEST STATUS: {request.status}</b>")
            return
        
    try:
        await bot.send_message(request.sender, text, reply_markup=reply_markup)
    except TelegramForbiddenError:
        await bot.send_message(
            request.approval_info["by"],
            f"⚠️ Помилка відправлення сповіщення щодо команди <b>{request.team_name}</b>: користувач заблокував бота!"
        )
    except Exception as e:
        await bot.send_message(
            request.approval_info["by"],
            f"⚠️ Помилка відправлення сповіщення щодо команди <b>{request.team_name}</b>: {e}"
        )

async def generate_request_info(request: Request, bot: Bot) -> str:
    approver_chat = await bot.get_chat(request.approval_info["by"])
    sender_chat = await bot.get_chat(request.sender)
    approved_time = datetime.fromtimestamp(request.approval_info["at"]).isoformat(sep=" ", timespec="minutes")

    match request.status:
        case RequestStatus.APPROVED:
            text = f"✅ <i>Запит на реєстрацію <b>{request.team_name}</b> (@{sender_chat.username}) було прийнято @{approver_chat.username} {approved_time}!</i>"
        case RequestStatus.DECLINED:
            text = f"⛔️ <i>Запит на реєстрацію <b>{request.team_name}</b> (@{sender_chat.username}) було відхилено @{approver_chat.username} {approved_time}!</i>"
        case RequestStatus.PENDING:
            text = f"⏳ <i>Рішення щодо <b>{request.team_name}</b> ще не прийнято!</i>"
        case _:
            text = f"⚠️ <b>UNSUPPORTED REQUEST STATUS: {request.status}</b>"

    return text


@approval_router.callback_query(F.data.startswith("request"), Approval.confirm)
async def block_approve_request(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    request = data.get("request")
    if request:
        await callback.answer(f"❗️ Спочатку підтвердь дію для команди {request.team_name}!")
    else:
        await callback.answer("⚠️ NO REQUEST!")

@approval_router.callback_query(F.data.startswith("request"))
async def approve_request(callback: types.CallbackQuery, state: FSMContext):
    message = callback.message
    _, action, request_id = callback.data.split(":")
    request = await Request.get(request_id)

    await state.update_data(request_message_text=message.text, request=request, approval_action=action)
    await state.set_state(Approval.confirm)

    if action == "approve":
        confirmation_message_text = f"Зареєструвати команду <b>{request.team_name}</b>?"
    else:
        confirmation_message_text = f"Відхилити реєстрацію команди <b>{request.team_name}</b>?"
        
    await message.edit_text(confirmation_message_text, reply_markup=confirmation_kb)

@approval_router.callback_query(Approval.confirm, F.data == "confirm")
async def confirm_request_approval(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    data = await state.get_data()

    # update the request data to check if it's still pending and not approved/declined by someone else
    request = await Request.get(data["request"].id)
    if request.status == RequestStatus.PENDING:
        by, at = callback.from_user.id, int(datetime.now().timestamp())
        if data["approval_action"] == "approve":
            await request.approve(approved_by=by, approved_at=at)
            await Team.create(request.sender, request.team_name)
        else:
            await request.decline(declined_by=by, declined_at=at)
        await send_approval_notificaition(request, bot)

    request_info = await generate_request_info(request, bot)
    await callback.message.edit_text(request_info)
    await state.set_state(None)

@approval_router.callback_query(Approval.confirm, F.data == "back")
async def cancel_request_approval(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    request_message_text = data["request_message_text"]
    request = data["request"]

    await callback.message.edit_text(request_message_text, reply_markup=request_approval_kb(str(request.id)))

    await state.set_state(None)
