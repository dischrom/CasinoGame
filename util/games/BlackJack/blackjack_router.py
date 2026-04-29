from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from . import blackjack
from util.users_data.database import get_balance, update_balance
from util import keyboard as kb

router = Router()


class BlackjackState(StatesGroup):
    """Состояния игры Блэкджека"""
    waiting_for_bet = State()
    game_started = State()
    choosing_action = State()


# Хранилище активных игр (в реальном приложении используйте БД)
active_games = {}


def get_game_keyboard(game_id: str) -> InlineKeyboardMarkup:
    """Клавиатура для игры"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Hit 🎴", callback_data=f"bj_hit_{game_id}"),
            InlineKeyboardButton(text="Stand 🛑", callback_data=f"bj_stand_{game_id}"),
        ],
        [InlineKeyboardButton(text="Double 2️⃣", callback_data=f"bj_double_{game_id}")],
    ])


@router.message(F.data == "blackjack")
async def start_blackjack(message: Message, state: FSMContext):
    """Начать игру в блэкджек"""
    user_id = message.from_user.id
    balance = await get_balance(user_id)

    if balance <= 0:
        await message.answer("❌ У вас нет фишек для игры!")
        return

    await state.set_state(BlackjackState.waiting_for_bet)
    await message.answer(
        f"💰 Ваш баланс: {balance} фишек\n\n"
        f"Введите размер ставки (1-{balance}):"
    )


@router.message(BlackjackState.waiting_for_bet)
async def set_bet(message: Message, state: FSMContext):
    """Установить ставку"""
    user_id = message.from_user.id

    try:
        bet = int(message.text)
    except ValueError:
        await message.answer("❌ Введите корректное число!")
        return

    balance = await get_balance(user_id)

    if bet <= 0 or bet > balance:
        await message.answer(f"❌ Ставка должна быть от 1 до {balance}")
        return

    # Создаём игру
    game = blackjack()
    game_id = f"{user_id}_{message.message_id}"
    active_games[game_id] = game

    # Вычитаем ставку из баланса
    await update_balance(user_id, balance - bet)

    # Начинаем игру
    game_info = game.start_game(bet)

    await state.set_state(BlackjackState.choosing_action)
    await state.update_data(game_id=game_id, bet=bet)

    await message.answer(
        game_info,
        reply_markup=get_game_keyboard(game_id)
    )


@router.callback_query(F.data.startswith("bj_hit_"))
async def hit(callback: CallbackQuery, state: FSMContext):
    """Взять карту"""
    game_id = callback.data.replace("bj_hit_", "")
    game = active_games.get(game_id)

    if not game:
        await callback.answer("❌ Игра не найдена!")
        return

    info, is_bust = game.hit()

    if is_bust:
        # Игра закончена
        data = await state.get_data()
        await callback.message.edit_text(info)
        active_games.pop(game_id, None)
        await state.clear()
    else:
        await callback.message.edit_text(info, reply_markup=get_game_keyboard(game_id))

    await callback.answer()


@router.callback_query(F.data.startswith("bj_stand_"))
async def stand(callback: CallbackQuery, state: FSMContext):
    """Остановиться"""
    game_id = callback.data.replace("bj_stand_", "")
    game = active_games.get(game_id)

    if not game:
        await callback.answer("❌ Игра не найдена!")
        return

    info, winnings = game.stand()
    user_id = callback.from_user.id
    balance = await get_balance(user_id)

    new_balance = balance + winnings
    await update_balance(user_id, new_balance)

    result_text = f"{info}\n\n💰 Новый баланс: {new_balance} фишек"

    await callback.message.edit_text(result_text)
    active_games.pop(game_id, None)
    await state.clear()
    await callback.answer()


@router.callback_query(F.data.startswith("bj_double_"))
async def double_down(callback: CallbackQuery, state: FSMContext):
    """Удвоить ставку"""
    game_id = callback.data.replace("bj_double_", "")
    game = active_games.get(game_id)

    if not game:
        await callback.answer("❌ Игра не найдена!")
        return

    # Проверяем баланс для удвоения
    user_id = callback.from_user.id
    balance = await get_balance(user_id)

    if balance < game.player_bet:
        await callback.answer("❌ Недостаточно фишек для удвоения!")
        return

    # Удваиваем ставку
    await update_balance(user_id, balance - game.player_bet)

    info, winnings = game.double_down()
    new_balance = await get_balance(user_id)
    new_balance += winnings
    await update_balance(user_id, new_balance)

    result_text = f"{info}\n\n💰 Новый баланс: {new_balance} фишек"

    await callback.message.edit_text(result_text)
    active_games.pop(game_id, None)
    await state.clear()
    await callback.answer()
