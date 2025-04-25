from utils import get_user, get_solo
from keyboards import replies
from bot.models import Contact


async def contact(update, context):
    contact = await get_solo(Contact)

    if contact and contact.body:
        await update.message.reply_text(
            contact.body,
            reply_markup=replies.get_main()
        )
        return
    
    await update.message.reply_text(
        "Kontakt ma'lumotlari topilmadi",
        reply_markup=replies.get_main(),
    )
    return
