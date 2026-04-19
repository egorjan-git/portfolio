import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
)

BOT_TOKEN = "8101654199:AAEpki607j4VzXiBhR-tza07YZvSxv31rAs"
WEBAPP_URL = "https://85-239-53-244.webapp.sslip.io/?v=20260212_01"

dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="Открыть мини-приложение",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    ]])
    await message.answer("Открой приложение:", reply_markup=kb)

async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(BOT_TOKEN)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
