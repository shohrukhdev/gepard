from utils import get_user, update_or_create
from keyboards import replies
import states
from telegram import Update
from telegram.ext import CallbackContext
from bot.models import TelegramUser
import re


@get_user
async def get_parameters(update: Update, context: CallbackContext, user: TelegramUser):
    message = f"F.I.O. <b>{user.get_full_name()}</b>\n"
    message += f"Telefon <b>{user.phone}</b>"
    await update.message.reply_html(
        message, 
        reply_markup=replies.get_settings()
    )
    return states.GET_SETTING


@get_user
async def get_setting(update: Update, context: CallbackContext, user: TelegramUser):

    setting = update.message.text

    if setting == "🪪 Ism va Familiyani tahrirlash":
        message = "Ism va Familiyangizni yuboring"
        await update.message.reply_text(message, reply_markup=replies.get_back())
        return states.GET_FULL_NAME

    if setting == "📞 Telefon raqamni tahrirlash":
        message = "Telefon raqamingizni +998901234567 shu formatda yuboring"
        await update.message.reply_text(message, reply_markup=replies.get_back())
        return states.GET_PHONE

    if setting == "◀️ Ortga qaytish":
        message = "Kerakli xizmatni tanlang"
        await update.message.reply_text(message, reply_markup=replies.get_main())
        return -1
    
    message = "Iltimos, kerakli bo'limni tugmalar orqali tanlang"
    await update.message.reply_text(message, reply_markup=replies.get_back())
    return states.GET_SETTING


@get_user
async def get_full_name(update: Update, context: CallbackContext, user: TelegramUser):
    if update.message.text == "◀️ Ortga qaytish":
        message = "Bosh menyu, kerakli xizmatni tanlang"
        await update.message.reply_text(message, reply_markup=replies.get_main())
        return -1

    full_name = str(update.message.text).split()
    first_name = None
    last_name = None

    if len(full_name) > 1:
        first_name = full_name[0]
        last_name = " ".join(full_name[1:])

    else:
        first_name = full_name[0]
    params = {"telegram_id":user.telegram_id}
    defaults = {"first_name":first_name, "last_name":last_name, "is_updated":True}
    await update_or_create(TelegramUser, params, defaults)

    message = "Ism va Familiya muvaffaqiyatli saqlandi, kerakli xizmatni tanlang"
    await update.message.reply_text(message, reply_markup=replies.get_main())
    return -1


@get_user
async def get_phone(update: Update, context: CallbackContext, user: TelegramUser):
    text = update.message.text

    if update.message.text == "◀️ Ortga qaytish":
        message = "Bosh menyu, kerakli xizmatni tanlang"
        await update.message.reply_text(message, reply_markup=replies.get_main())
        return -1
    

    if re.match("^\+998\d{9}$", text):
        user.phone = text
        await user.asave(update_fields=['phone'])
        message = "Telefon raqam yangilandi, kerakli xizmatni tanlang"
        await update.message.reply_text(message, reply_markup=replies.get_main())
        return -1
        
    await update.message.reply_text(
        "Telefon raqamingizni +998901234567 shu formatda yuboring",
        reply_markup=replies.get_back()
    )
    return states.GET_PHONE