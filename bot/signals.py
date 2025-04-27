import os
from django.dispatch import receiver
from django.db.models.signals import pre_save
from bot.models import Order, Product
from datetime import datetime
from dotenv import load_dotenv
import requests
from django.contrib import messages

load_dotenv()


@receiver(pre_save, sender=Order)
def update_approve_time(sender, instance:Order, **kwargs):
    if instance.pk:
        old_instance = Order.objects.get(id=instance.pk)
        if old_instance.status == Order.OrderStatus.APPROVED_BY_DIRECTOR and old_instance.status != instance.status:
            for item in instance.items.all():
                try:
                    product = Product.objects.get(id=item)
                    product.amount = int(product.amount) - int(item.qty)
                    product.save(update_fields=['amount'])
                except:
                    pass
            return

        if ((old_instance.status == Order.OrderStatus.PENDING and instance.status == Order.OrderStatus.CANCELLED) or
            (old_instance.status == Order.OrderStatus.APPROVED_BY_ACCOUNTANT and instance.status == Order.OrderStatus.CANCELLED) or
            (old_instance.status == Order.OrderStatus.APPROVED_BY_DIRECTOR and instance.status == Order.OrderStatus.CANCELLED) or
            (old_instance.status == Order.OrderStatus.APPROVED_BY_STOREKEEPER and instance.status == Order.OrderStatus.CANCELLED)):
            message = "Заказ был отменен\n"
            message = f"Заказ Nº {str(instance.id).zfill(5)}"
            return


def cancel_order_message(order: Order, confirmer):
    CANCELERS = {
        "rop": "Отказано руководителем отдела продаж",
        "director": "Отказано директором",
        "accountant": "Отказано бухгалтером",
        "storekeeper": "Отказано кладовщиком"
    }

    order_user_first_name = order.user.first_name if order.user else "Не указано"
    order_user_last_name = order.user.last_name if order.user else "Не указано"
    message = f"<b>Заказ Nº {str(order.id).zfill(5)},</b>\n"
    message += f"<b>Клиент:</b> {order_user_first_name} {order_user_last_name}\n"
    message += f"<b>Статус:</b> ❌ {CANCELERS[confirmer]}\n"
    message += "===================== \n\n"
    total_sum_uzs = 0
    for item in order.items.all():
        total_sum_uzs += float(item.qty) * float(item.price_uzs)

        message += f"{item.product_name} - {item.qty} шт. {item.set_amount} набор\n\n"

    order_comment = order.comment if order.comment else "Не указано"
    if order.agent and order.agent.territory.exists():
        order_area = ", ".join([territory.name for territory in order.agent.territory.all()])
    else:
        order_area = "Не указано"

    message += f"<b>Комментарий:</b> {order_comment}\n"
    message += f"<b>Территории:</b> {order_area}\n"
    message += "\n=====================\n"
    message += f"<b>Общая сумма (UZS):</b> {total_sum_uzs:,}\n"
    return message


def make_order_message(order: Order, confirmer):
    CONFIRMERS = {
        "rop": "Подтверждено руководителем отдела продаж",
        "director": "Подтверждено директором",
        "accountant":"Подтверждено бухгалтером",
        "storekeeper": "Подтверждено кладовщиком"
    }

    order_user_first_name = order.user.first_name if order.user else "Не указано"
    order_user_last_name = order.user.last_name if order.user else "Не указано"
    message = f"<b>Заказ Nº {str(order.id).zfill(5)},</b>\n"
    message += f"<b>Клиент:</b> {order_user_first_name} {order_user_last_name}\n"
    message += f"<b>Статус:</b> ✅ {CONFIRMERS[confirmer]}\n"
    message += "===================== \n\n"
    total_sum_uzs = 0
    for item in order.items.all():
        total_sum_uzs += float(item.qty) * float(item.price_uzs)

        message += f"{item.product_name} - {item.qty} шт. {item.set_amount} набор\n\n"

    order_comment = order.comment if order.comment else "Не указано"
    if order.agent and order.agent.territory.exists():
        agent_territory = ", ".join([territory.name for territory in order.agent.territory.all()])
    else:
        agent_territory = "Не указано"

    message += f"<b>Комментарий:</b> {order_comment}\n"
    message += f"<b>Территории:</b> {agent_territory}\n"
    message += "\n=====================\n"
    message += f"<b>Общая сумма (UZS):</b> {total_sum_uzs:,}\n"
    return message


def send_notification(chat_id, message):
    token = os.environ.get("TOKENS")
    if token:
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        endpoint = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(endpoint, data=data)
    else:
        raise Exception(f"Token not found {token}")
