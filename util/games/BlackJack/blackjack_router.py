from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .blackjack import BlackjackGame
from util.users_data.database import get_balance, update_balance
from util import keyboard as kb

router = Router()


class BlackjackState(StatesGroup):
    """Состояния игры Блэкджека"""
    waiting_for_bet = State()
    choosing_action = State()


active_games = {}


def get_game_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для игры"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Hit 🎴", callback_data=f"bj_hit_{user_id}"),
            InlineKeyboardButton(text="Stand 🛑", callback_data=f"bj_stand_{user_id}"),
        ],
        [InlineKeyboardButton(text="Double 2️⃣", callback_data=f"bj_double_{user_id}")],
    ])


async def end_game(user_id: int, state: FSMContext):
    """Завершить игру"""
    active_games.pop(str(user_id), None)
    await state.clear()


@router.callback_query(F.data == "blackjack")
async def start_blackjack(callback: CallbackQuery, state: FSMContext):
    """Начать игру в блэкджек"""
    user_id = callback.from_user.id

    try:
        balance = await get_balance(user_id)
    except Exception:
        await callback.answer("❌ Ошибка БД!", show_alert=True)
        return

    if balance <= 0:
        await callback.answer("❌ У вас нет фишек!", show_alert=True)
        return

    await state.set_state(BlackjackState.waiting_for_bet)
    await callback.message.answer(
        f"💰 Баланс: {balance} фишек\n\n"
        f"Введите ставку (1-{balance}):"
    )
    await callback.answer()


@router.message(BlackjackState.waiting_for_bet)
async def set_bet(message: Message, state: FSMContext):
    """Установить ставку"""
    user_id = message.from_user.id

    try:
        bet = int(message.text)
    except ValueError:
        await message.answer("❌ Введите число!")
        return

    try:
        balance = await get_balance(user_id)
    except Exception:
        await message.answer("❌ Ошибка БД!")
        return

    if bet <= 0 or bet > balance:
        await message.answer(f"❌ Ставка должна быть 1-{balance}")
        return

    # Создаём игру
    game = BlackjackGame()
    game_id = str(user_id)
    active_games[game_id] = game

    # Вычитаем ставку
    try:
        await update_balance(user_id, balance - bet)
    except Exception:
        await message.answer("❌ Ошибка обновления баланса!")
        active_games.pop(game_id, None)
        return

    await state.set_state(BlackjackState.choosing_action)
    await state.update_data(bet=bet)

    game_info = game.start_game(bet)

    if game.player_hand.is_blackjack():
        # Автоматический выигрыш при блэкджеке
        winnings = int(bet * 2.5)
        try:
            new_balance = (balance - bet) + winnings
            await update_balance(user_id, new_balance)
        except Exception:
            pass

        await message.answer(
            f"{game_info}\n\n💰 Новый баланс: {new_balance} фишек"
        )
        await end_game(user_id, state)
    else:
        await message.answer(game_info, reply_markup=get_game_keyboard(user_id))


@router.callback_query(F.data.startswith("bj_hit_"))
async def hit(callback: CallbackQuery, state: FSMContext):
    """Взять карту"""
    user_id = int(callback.data.replace("bj_hit_", ""))
    game = active_games.get(str(user_id))

    if not game:
        await callback.answer("❌ Игра не найдена!", show_alert=True)
        return

    info, is_bust = game.hit()

    if is_bust:
        await callback.message.edit_text(info)
        await end_game(user_id, state)
    else:
        await callback.message.edit_text(info, reply_markup=get_game_keyboard(user_id))

    await callback.answer()


@router.callback_query(F.data.startswith("bj_stand_"))
async def stand(callback: CallbackQuery, state: FSMContext):
    """Остановиться"""
    user_id = int(callback.data.replace("bj_stand_", ""))
    game = active_games.get(str(user_id))

    if not game:
        await callback.answer("❌ Игра не найдена!", show_alert=True)
        return

    info, winnings = game.stand()

    try:
        balance = await get_balance(user_id)
        new_balance = balance + winnings
        await update_balance(user_id, new_balance)
    except Exception:
        await callback.answer("❌ Ошибка БД!", show_alert=True)
        return

    result = f"{info}\n\n💰 Новый баланс: {new_balance} фишек"
    await callback.message.edit_text(result, reply_markup=kb.blackjack_kb)
    await end_game(user_id, state)
    await callback.answer()


@router.callback_query(F.data.startswith("bj_double_"))
async def double_down(callback: CallbackQuery, state: FSMContext):
    """Удвоить ставку"""
    user_id = int(callback.data.replace("bj_double_", ""))
    game = active_games.get(str(user_id))

    if not game:
        await callback.answer("❌ Игра не найдена!", show_alert=True)
        return

    data = await state.get_data()
    bet = data.get("bet", 0)

    try:
        balance = await get_balance(user_id)
    except Exception:
        await callback.answer("❌ Ошибка БД!", show_alert=True)
        return

    if balance < bet:
        await callback.answer("❌ Не хватает фишек!", show_alert=True)
        return

    # Вычитаем доп. ставку
    try:
        await update_balance(user_id, balance - bet)
    except Exception:
        await callback.answer("❌ Ошибка обновления!", show_alert=True)
        return

    info, is_finished = game.double()

    if is_finished:
        # Рассчитываем выигрыш
        player_value = game.player_hand.get_value()
        dealer_value = game.dealer_hand.get_value()

        if game.dealer_hand.is_bust():
            winnings = game.player_bet * 2
        elif player_value > dealer_value:
            winnings = game.player_bet * 2
        elif player_value == dealer_value:
            winnings = game.player_bet
        else:
            winnings = 0

        try:
            current_balance = await get_balance(user_id)
            new_balance = current_balance + winnings
            await update_balance(user_id, new_balance)
        except Exception:
            new_balance = current_balance

        result = f"{info}\n\n💰 Новый баланс: {new_balance} фишек"
        await callback.message.edit_text(result, reply_markup=kb.blackjack_kb)
        await end_game(user_id, state)
    else:
        await callback.message.edit_text(info, reply_markup=get_game_keyboard(user_id))

    await callback.answer()


@router.callback_query(F.data == "back_in_blackjack")
async def back_in_blackjack(callback: CallbackQuery, state: FSMContext):
    """Вернуться в меню"""
    user_id = callback.from_user.id
    await end_game(user_id, state)

    await callback.message.edit_text(
        "🎰 Главное меню",
        reply_markup=kb.games_kb
    )
    await callback.answer()
