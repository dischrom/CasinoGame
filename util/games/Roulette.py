import asyncio
import random
from aiogram.types import Message, CallbackQuery
from aiogram import Router, F
from .. import keyboard as kb
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from users_data.database import get_balance, update_balance, add_user
from util.start import start


router = Router()


class Roulette(StatesGroup):
    bet_type = State()
    stavka = State()
    color = State()
    number = State()


@router.callback_query(F.data == "roulette")
async def roulette(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    balance = await get_balance(user_id)

    if balance <= 0:
        await callback.message.answer(
            f"❌ You have no chips! (Balance: {balance})\n"
            "Come back tomorrow for daily rewards!"
        )
        await callback.answer()
        return

    await state.set_state(Roulette.bet_type)
    await callback.message.answer(
        f"💰 Your balance: {balance} chips\n\n"
        "Choose your bet type:\n"
        "1️⃣ Color only (Red/Black)\n"
        "2️⃣ Number only (0-36)\n"
        "3️⃣ Both color and number",
        reply_markup=kb.roulette_bet_type_kb
    )
    await callback.answer()


@router.callback_query(F.data.startswith("bet_"), Roulette.bet_type)
async def select_bet_type(callback: CallbackQuery, state: FSMContext):
    bet_type = callback.data.split("_")[1]
    user_id = callback.from_user.id
    balance = await get_balance(user_id)

    await state.update_data(bet_type=bet_type)
    await state.set_state(Roulette.stavka)
    await callback.message.answer(
        f"💰 Your balance: {balance} chips\n\n"
        "Enter your bet amount (in chips):"
    )
    await callback.answer()


@router.message(Roulette.stavka)
async def enter_stavka(message: Message, state: FSMContext):
    user_id = message.from_user.id
    balance = await get_balance(user_id)

    try:
        bet_amount = int(message.text)

        if bet_amount <= 0:
            await message.answer("❌ Bet must be greater than 0!")
            return

        if bet_amount > balance:
            await message.answer(
                f"❌ Insufficient balance!\n"
                f"Your balance: {balance} chips\n"
                f"Your bet: {bet_amount} chips"
            )
            return

        await state.update_data(bet_amount=bet_amount)
        data = await state.get_data()
        bet_type = data['bet_type']

        if bet_type == "color":
            await state.set_state(Roulette.color)
            await message.answer(
                f"Bet: {bet_amount} chips on COLOR\n"
                "Choose color:\n"
                "🔴 Red\n"
                "⚫ Black",
                reply_markup=kb.roulette_color_kb
            )
        elif bet_type == "number":
            await state.set_state(Roulette.number)
            await message.answer(f"Bet: {bet_amount} chips on NUMBER\nEnter a number (0-36):")
        else:  # both
            await state.set_state(Roulette.color)
            await message.answer(
                f"Bet: {bet_amount} chips on COLOR + NUMBER\n"
                "First, choose color:\n"
                "🔴 Red\n"
                "⚫ Black",
                reply_markup=kb.roulette_color_kb
            )
    except ValueError:
        await message.answer("❌ Please enter a valid number!")


@router.callback_query(F.data.startswith("color_"), Roulette.color)
async def select_color(callback: CallbackQuery, state: FSMContext):
    color = callback.data.split("_")[1]
    user_id = callback.from_user.id
    await state.update_data(color=color)
    data = await state.get_data()

    if data['bet_type'] == "color":
        result = spin_color(color, data['bet_amount'])

        # Обнови баланс
        if result['payout'] > 0:
            await update_balance(user_id, result['payout'] - data['bet_amount'])
        else:
            await update_balance(user_id, -data['bet_amount'])

        new_balance = await get_balance(user_id)

        await callback.message.answer(
            f"🎡 Wheel spun!\n"
            f"Your bet: {color.upper()}\n"
            f"Winning number: {result['win_num']} ({result['win_color'].upper()})\n"
            f"Result: {result['message']}\n"
            f"Payout: {result['payout']} chips\n"
            f"💰 New balance: {new_balance} chips",
            reply_markup=kb.roulette_play_again_kb
        )
        await state.clear()
    else:
        await state.set_state(Roulette.number)
        await callback.message.answer(
            f"Selected color: {color.upper()}\n"
            f"Now enter a number (0-36):"
        )

    await callback.answer()


@router.message(Roulette.number)
async def enter_number(message: Message, state: FSMContext):
    user_id = message.from_user.id

    try:
        number = int(message.text)
        if number < 0 or number > 36:
            await message.answer("❌ Number must be between 0 and 36!")
            return

        data = await state.get_data()
        bet_type = data['bet_type']
        bet_amount = data['bet_amount']

        if bet_type == "number":
            result = spin_number(number, bet_amount)

            # Обнови баланс
            if result['payout'] > 0:
                await update_balance(user_id, result['payout'] - bet_amount)
            else:
                await update_balance(user_id, -bet_amount)

            new_balance = await get_balance(user_id)

            await message.answer(
                f"🎡 Wheel spun!\n"
                f"Your number: {number}\n"
                f"Winning number: {result['win_num']}\n"
                f"Result: {result['message']}\n"
                f"Payout: {result['payout']} chips\n"
                f"💰 New balance: {new_balance} chips",
                reply_markup=kb.roulette_play_again_kb
            )
        else:  # both
            color = data['color']
            result = spin_both(number, color, bet_amount)

            # Обнови баланс
            if result['payout'] > 0:
                await update_balance(user_id, result['payout'] - bet_amount)
            else:
                await update_balance(user_id, -bet_amount)

            new_balance = await get_balance(user_id)

            await message.answer(
                f"🎡 Wheel spun!\n"
                f"Your bet: {color.upper()} + {number}\n"
                f"Winning number: {result['win_num']} ({result['win_color'].upper()})\n"
                f"Result: {result['message']}\n"
                f"Payout: {result['payout']} chips\n"
                f"💰 New balance: {new_balance} chips",
                reply_markup=kb.roulette_play_again_kb
            )

        await state.clear()
    except ValueError:
        await message.answer("❌ Please enter a valid number (0-36)!")


@router.callback_query(F.data == "play_again")
async def play_again(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    balance = await get_balance(user_id)

    if balance <= 0:
        await callback.message.answer(
            f"❌ You have no chips! (Balance: {balance})\n"
            "Come back tomorrow for daily rewards!"
        )
        await callback.answer()
        return

    await state.set_state(Roulette.bet_type)
    await callback.message.edit_text(
        f"💰 Your balance: {balance} chips\n\n"
        "Choose your bet type:\n"
        "1️⃣ Color only (Red/Black)\n"
        "2️⃣ Number only (0-36)\n"
        "3️⃣ Both color and number",
        reply_markup=kb.roulette_bet_type_kb
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🎮 Games menu",
        reply_markup=kb.games_kb
    )
    await callback.answer()


@router.callback_query(F.data == "back_in_games")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    # ✅ Получаем данные из callback, а не из message
    user_id = callback.from_user.id
    username = callback.from_user.username
    first_name = callback.from_user.first_name

    result = await add_user(user_id, username or first_name)
    balance = await get_balance(user_id)

    if result:
        status = "✨ Новый пользователь добавлен!"
    else:
        status = "👋 С возвращением!"

    await callback.message.answer(
        f"Welcome! {first_name} {status}\n"
        f"💰 Balance: {balance} chips",
        reply_markup=kb.start_kb
    )
    await callback.answer()


# ========== SPIN FUNCTIONS ==========

def get_color(number: int) -> str:
    if number == 0:
        return "green"
    black_nums = (2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 29, 31, 33, 35)
    return "black" if number in black_nums else "red"


def spin_color(color: str, bet_amount: int) -> dict:
    win_num = random.randint(0, 36)
    win_color = get_color(win_num)

    if color == win_color:
        payout = bet_amount * 2
        return {
            "win_num": win_num,
            "win_color": win_color,
            "message": f"✅ {color.upper()} wins!",
            "payout": payout
        }

    return {
        "win_num": win_num,
        "win_color": win_color,
        "message": f"❌ You lost! {win_color.upper()} won.",
        "payout": 0
    }


def spin_number(number: int, bet_amount: int) -> dict:
    win_num = random.randint(0, 36)

    if number == win_num:
        payout = bet_amount * 36
        return {
            "win_num": win_num,
            "message": "🎉 YOU WIN!",
            "payout": payout
        }

    return {
        "win_num": win_num,
        "message": "❌ You lost!",
        "payout": 0
    }


def spin_both(number: int, color: str, bet_amount: int) -> dict:
    win_num = random.randint(0, 36)
    win_color = get_color(win_num)

    if number == win_num:
        payout = bet_amount * 36
        return {
            "win_num": win_num,
            "win_color": win_color,
            "message": f"🎉 EXACT MATCH! Number {number} won!",
            "payout": payout
        }

    if color == win_color:
        payout = bet_amount * 2
        return {
            "win_num": win_num,
            "win_color": win_color,
            "message": f"✅ Color match! {color.upper()} won.",
            "payout": payout
        }

    return {
        "win_num": win_num,
        "win_color": win_color,
        "message": "❌ You lost!",
        "payout": 0
    }


@router.callback_query(F.data == "play_again")
async def play_again_number(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Roulette.bet_type)
    await callback.message.edit_text(
        "Choose your bet type:\n"
        "1️⃣ Color only (Red/Black)\n"
        "2️⃣ Number only (0-36)\n"
        "3️⃣ Both color and number",
        reply_markup=kb.roulette_bet_type_kb)
    await callback.answer()

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Choice a game: ",
                                  reply_markup=kb.games_kb)





