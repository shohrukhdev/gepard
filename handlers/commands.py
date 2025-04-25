from utils import get_user
from telegram import ReplyKeyboardMarkup
from keyboards import replies
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

import os
from dotenv import load_dotenv

load_dotenv()


@get_user
async def start(update, context, user):
    message = "Здравствуйте, добро пожаловать в наш бот. \nВыберите нужную услугу."

    if user.is_agent:
        return await update.message.reply_text(
            message, reply_markup=replies.get_agent_main()
        )
    await update.message.reply_text(message, reply_markup=replies.get_main())
    return -1


@get_user
async def category(update, context, user):
    if not user.is_agent:
        return await start(update, context, user)
    
    base_url = os.environ.get("WEBAPP")
    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton(
                text="Стандарт Цена (сум)", 
                web_app=WebAppInfo(url=f"{base_url}?cate=a&preview=1")
            ),
            InlineKeyboardButton(
                text="Excel", 
                callback_data="a"
            )
        ],
        [
            InlineKeyboardButton(
                text="-4% Цена (сум)", 
                web_app=WebAppInfo(url=f"{base_url}?cate=b&preview=1")
            ),
            InlineKeyboardButton(
                text="Excel", 
                callback_data="b"
            )
        ],
        [
            InlineKeyboardButton(
                text="Хорека Цена (сум)", 
                web_app=WebAppInfo(url=f"{base_url}?cate=c&preview=1")
            ),
            InlineKeyboardButton(
                text="Excel", 
                callback_data="c"
            )
        ],
        [
            InlineKeyboardButton(
                text="Оптовик Цена (сум)", 
                web_app=WebAppInfo(url=f"{base_url}?cate=d&preview=1")
            ),
            InlineKeyboardButton(
                text="Excel", 
                callback_data="d"
            )
        ],
        [
            InlineKeyboardButton(
                text="-2% Цена (сум)", 
                web_app=WebAppInfo(url=f"{base_url}?cate=e&preview=1")
            ),
            InlineKeyboardButton(
                text="Excel", 
                callback_data="e"
            )
        ]]
    )
    return await update.message.reply_text("Выберите категорию",reply_markup=keyboard)
    
    