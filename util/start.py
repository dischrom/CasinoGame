from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram import Router, F
from . import keyboard as kb
from users_data.database import  add_user, get_balance

router = Router()


@router.message(CommandStart())
async def start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    result = await add_user(user_id, username or first_name)
    balance = await get_balance(user_id)

    if result:
        status = "✨ Новый пользователь добавлен!"
    else:
        status = "👋 С возвращением!"

    await message.answer(
        f"Welcome! {first_name} {status}\n"
        f"💰 Balance: {balance} chips",
        reply_markup=kb.start_kb
    )

@router.callback_query(F.data == "games")
async def games_callback(callback: CallbackQuery):
    await callback.message.answer("Choice a game: ",
                                  reply_markup=kb.games_kb)
    await callback.answer()

@router.callback_query(F.data == "balance")
async def balance_callback(callback: CallbackQuery):
    balance = await get_balance(callback.from_user.id)
    await callback.message.answer(f"Balance: {balance} 💰")
    await callback.answer()