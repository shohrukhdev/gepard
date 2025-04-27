from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from bot.models import Order


def get_user_inline_keyboard(users):
    keyboard = []
    for user in users:
        button = InlineKeyboardButton(text=f"{user.first_name} {user.last_name or ''}",
                                      callback_data=f"order_{user.id}")
        keyboard.append([button])

    keyboard.append([InlineKeyboardButton("Назад", callback_data="back")])
    return InlineKeyboardMarkup(keyboard)


def create_payment_keyboard():
    PaymentTypes = Order.PaymentTypes
    keyboard = [
        [InlineKeyboardButton(PaymentTypes.CASH.label, callback_data=PaymentTypes.CASH.value)],
        [InlineKeyboardButton(PaymentTypes.TRANSFER.label, callback_data=PaymentTypes.TRANSFER.value)],
        [InlineKeyboardButton(PaymentTypes.OTHER.label, callback_data=PaymentTypes.OTHER.value)]
    ]
    return InlineKeyboardMarkup(keyboard)
