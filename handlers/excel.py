from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, ContextTypes
from openpyxl import Workbook
from django.conf import settings
from bot.models import Product  # Import your Product model
import os
from asgiref.sync import sync_to_async
import asyncio

@sync_to_async
def fetch_products(cat):
    # Use extra() to select dynamic fields for prices
    return list(Product.objects.extra(
        select={
            'price_uzs': f'price_uzs_{cat}',
            'price_usd': f'price_usd_{cat}'
        }
    ).values('id', 'title', 'price_uzs', 'price_usd'))

# Function to generate Excel file from Product data
async def generate_excel_file(cat):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Products"

    products = await fetch_products(cat)

    headers = [
        "ID", "Название продукта", "Цена (сум)"
    ]
    sheet.append(headers)

    for product in products:
        sheet.append([product.get("id"), product.get("title"), product.get("price_uzs")])

    # Save the workbook to a temporary file
    file_path = os.path.join(settings.BASE_DIR, "products.xlsx")
    workbook.save(file_path)

    return file_path

# Bot handler to send the Excel file
async def send_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Generate the Excel file
    category = update.callback_query.data
    file_path = await generate_excel_file(category)

    await update.callback_query.answer()
    await update.callback_query.message.reply_text("Файл создается...")
    await update.callback_query.message.delete()

    # Send the file to the user
    with open(file_path, 'rb') as file:
        await context.bot.send_document(
            chat_id=update.effective_chat.id,  # Send to the chat where the command was received
            document=InputFile(file, filename="products.xlsx"),  # Opened file as InputFile
            caption="Here is the list of products."  # Optional caption
        )

    # Optionally, delete the file if it's a temporary file
    os.remove(file_path)
