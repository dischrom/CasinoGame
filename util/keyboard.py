
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

start_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Games", callback_data="games"), InlineKeyboardButton(text="Balance", callback_data="balance")]
])
games_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Roulette", callback_data="roulette"), InlineKeyboardButton(text="Black Jack", callback_data="blackjack")],
    [InlineKeyboardButton(text="Back", callback_data="back_in_games")]
])

balance_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Balance", callback_data="balance")],
    [InlineKeyboardButton(text="Back", callback_data="back_in_balance")]
])



#-----------------ROULETTE KEYBOARDS-----------------------------------------------------------
roulette_bet_type_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="1️⃣ Color Only", callback_data="bet_color")],
    [InlineKeyboardButton(text="2️⃣ Number Only", callback_data="bet_number")],
    [InlineKeyboardButton(text="3️⃣ Both", callback_data="bet_both")]
])

# For color selection
roulette_color_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔴 Red", callback_data="color_red")],
    [InlineKeyboardButton(text="⚫ Black", callback_data="color_black")]
])

roulette_play_again_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Play Again", callback_data="play_again"), InlineKeyboardButton(text="Back to menu", callback_data="back_to_menu")]
])



#-----------------ROULETTE KEYBOARDS-----------------------------------------------------------

#====================BLACK JACK KEYBOARDS======================================================

blackjack_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Back", callback_data="back_in_blackjack"), InlineKeyboardButton(text="Back to menu", callback_data="back_to_menu")]
])
#=========================BLACK JACK KEYBOARDS=================================================