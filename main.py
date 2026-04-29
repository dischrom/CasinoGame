import logging
import asyncio
from aiogram import Dispatcher, Bot
from util.games import routers
from users_data.database import init_db

from config import TOKEN

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

for router in routers:
    dp.include_router(router)

async def main():
    await init_db()
    await dp.start_polling(bot)  # Add await here!


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Shutting down")
