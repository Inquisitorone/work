import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
if not API_TOKEN:
    raise RuntimeError("Set TELEGRAM_API_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler()
async def echo(message: types.Message):
    await message.answer(f"Echo: {message.text}")

if __name__ == '__main__':
    
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
