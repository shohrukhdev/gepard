from utils import get_user, update_or_create
from keyboards import replies, inlines
import json
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import CallbackContext
from bot.models import TelegramUser, Order, OrderItem, Product
import states
from asgiref.sync import sync_to_async
from django.db.models import Q

# async def get_telegram_users(user):
#     from django.db import close_old_connections
#     close_old_connections()
#     return await sync_to_async(lambda: TelegramUser.objects.filter(territory__in=user.territory.all(), is_agent=False))()

async def fetch_clients(territories, search):
    # Wrap the ORM operation with sync_to_async
    return await sync_to_async(
        lambda: list(
            TelegramUser.objects.filter(
                Q(first_name__icontains=search) | Q(tin__icontains=search),
                territory__in=territories,
                is_agent=False,
                is_active=True
            )
        )
    )()

@get_user
async def web_app_data(update: Update, context: CallbackContext, user: TelegramUser) -> None:
    data = json.loads(update.effective_message.web_app_data.data)

    if not user.is_agent:
        await update.message.reply_html(
            text="Sizda buyurtma berish ruxsati mavjud emas. \nKerakli xizmatni tanlang",
            reply_markup=replies.get_main()
        )
        return -1
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    if not longitude or not latitude:
        await update.message.reply_text(
            text="Заказ отменен, поскольку с устройства не было получено местоположение.",
            reply_markup=replies.get_agent_main()
        )
        return -1

    location_path = f"https://www.google.com/maps?q={latitude},{longitude}&ll={latitude},{longitude}&z=16"
    order = await Order.objects.acreate(user=user, location_path=location_path)
    order_items = []
    
    for item in data['data']:
        try:
            product = await Product.objects.aget(id=item['id'])
            order_items.append(
                OrderItem(
                    order=order,
                    product_name=product.title,
                    product_in_set=product.set_amount,
                    product_id=product.pk,
                    qty=item['qty'],
                    set_amount=item['set'],
                    price_uzs=item['price_uzs']
                )
            )

        except Product.DoesNotExist:
            continue

    if order_items:
        await OrderItem.objects.abulk_create(order_items)
    
    context.user_data["uncompleted_order_id"] = order.pk
    territories = await sync_to_async(user.territory.all)()
    clients = await fetch_clients(territories, search="")
    if not clients:
        message = "Заказ отменен, так как у вас нет клиентов"
        await order.adelete()
        await update.message.reply_text(message, reply_markup=replies.get_agent_main())
        return -1

    if not context.user_data.get("client_for_order"):
        message = "Выберите клиента"
        await update.message.reply_text(message, reply_markup=inlines.get_user_inline_keyboard(clients))
        
        return states.CHOOSE_CLIENT
    
    client = await TelegramUser.objects.aget(id=context.user_data.get("client_id_for_order"))
    order.user = client
    order.agent = user
    order.comment = data.get("comment")
    await order.asave()
    
    del context.user_data["client_for_order"]
    del context.user_data["client_id_for_order"]

    message = "Выберите тип оплаты"
    await update.message.reply_text(message, reply_markup=inlines.create_payment_keyboard())
    return states.CHOOSE_PAYMENT


@get_user
async def get_agent_client(update, context, user):
    territories = await sync_to_async(user.territory.all)()
    clients = await fetch_clients(territories, search="")
    if not clients:
        message = "У вас нет клиентов"
        await update.message.reply_text(message, reply_markup=replies.get_agent_main())
        return -1

    message = "Поиск по имени клиента / ИНН клиента"
    await update.message.reply_text(message, reply_markup=replies.get_back_ru())
    context.user_data["client_for_order"] = True

    # return states.CHOOSE_CLIENT
    return states.SEARCH_CLIENT


@get_user
async def get_searched_user(update: Update, context: CallbackContext, user: TelegramUser) -> None:
    if update.message and update.message.text:
        if update.message.text == "◀️ Назад":
            await update.message.reply_text("Главное меню", reply_markup=replies.get_agent_main())
            return -1
        message = "Выберите клиента или введите другой поиск"
        territories = await sync_to_async(user.territory.all)()
        clients = await fetch_clients(territories, search=update.message.text)
        if not clients:
            await update.message.reply_text("Результаты поиска не найдены, попробуйте еще раз", reply_markup=replies.get_back_ru())
            return states.SEARCH_CLIENT

        await update.message.reply_text(message, reply_markup=inlines.get_user_inline_keyboard(clients))
        return states.SEARCH_CLIENT
    
    elif update.callback_query and update.callback_query.data:
        return await get_client(update, context)
        


@get_user
async def get_client(update: Update, context: CallbackContext, user:TelegramUser) -> None:
    if update.message:
        return await get_agent_client(update, context)

    data = update.callback_query.data
    await update.callback_query.answer()
    await update.callback_query.delete_message()
    if data == 'back':
        await update.callback_query.message.reply_text("Выберите меню", reply_markup=replies.get_agent_main())
        return -1

    client_id = data.split("_")[1]
    client = await TelegramUser.objects.aget(id=client_id)
    if context.user_data.get("client_for_order"):
        context.user_data['client_id_for_order'] = client_id
        message = "Выберите желаемую услугу"
        await update.callback_query.message.reply_text(message, reply_markup=replies.get_main(client_id))
        return -1

    order = await Order.objects.aget(id=context.user_data['uncompleted_order_id'])
    order.user = client
    order.agent = user
    order.asave()

    message = "Выберите тип оплаты"
    await update.callback_query.message.reply_text(message, reply_markup=inlines.create_payment_keyboard())
    return states.CHOOSE_PAYMENT


@get_user
async def get_payment(update: Update, context: CallbackContext, user:TelegramUser):
    data = update.callback_query.data
    order = await Order.objects.aget(id=context.user_data['uncompleted_order_id'])
    order.payment_type = data
    await order.asave()
    await update.callback_query.delete_message()

    user = await TelegramUser.objects.aget(id=order.user_id)

    message = "<b>Заказ выполнен успешно</b>\n"
    message += f"<b>Клиент:</b> {user.first_name} {user.last_name}\n"
    message += f"<b>Статус:</b> {order.get_status_display()}\n"
    message += "===================== \n\n"
    total_sum_uzs = 0
    async for item in order.items.all().aiterator():
        total_sum_uzs += float(item.qty) * float(item.price_uzs)

        message += f"{item.product_name} - {item.qty} шт. {item.set_amount} блок\n"
    message += "\n=====================\n"
    message += f"<b>Общая сумма (UZS):</b> {total_sum_uzs:,}\n"
    
    if total_sum_uzs > user.limit:
        order.adelete()
        message = "Заказ отменен, так как баланс клиента превысил лимит"
    
    await update.callback_query.message.reply_text(message, reply_markup=replies.get_agent_main(), parse_mode="html")
    return -1


@get_user
async def get_location(update: Update, context: CallbackContext, user:TelegramUser):
    if update.message and update.message.location:
        location = update.message.location
        longitude = location.longitude
        latitude = location.latitude
        
        order = await Order.objects.aget(id=context.user_data['uncompleted_order_id'])
        user = await TelegramUser.objects.aget(id=order.user_id)
        await order.asave()
        message = "<b>Заказ выполнен успешно</b>\n"
        message += f"<b>Клиент:</b> {user.first_name} {user.last_name}\n"
        message += f"<b>Статус:</b> {order.get_status_display()}\n"
        message += "===================== \n\n"
        total_sum_uzs = 0
        order = await Order.objects.aget(id=context.user_data['uncompleted_order_id'])
        async for item in order.items.all().aiterator():
            total_sum_uzs += float(item.qty) * float(item.price_uzs)

            message += f"{item.product_name} - {item.qty} шт. {item.set_amount} блок\n"
        message += "\n=====================\n"
        message += f"<b>Общая сумма (UZS):</b> {total_sum_uzs:,}\n"

        if total_sum_uzs > user.limit:
            order.adelete()
            message = "Заказ отменен, так как баланс клиента превысил лимит"
        
        await update.message.reply_text(message, reply_markup=replies.get_agent_main(), parse_mode="html")
        return -1
    
    message = "Пожалуйста, отправьте местоположение с помощью кнопки"
    
    await update.message.reply_text(message, reply_markup=replies.get_location())
    return states.CHOOSE_LOCATION

