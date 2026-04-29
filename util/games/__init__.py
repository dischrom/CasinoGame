from .Roulette import router as roulette_router
from util.start import router as start_router
from BlackJack.blackjack_router import router as blackjack_router

routers = [roulette_router,
           start_router,
           blackjack_router]





