from django.http import HttpResponse
from django.template.loader import render_to_string
# from weasyprint import HTML, CSS
from .models import Order
from PyPDF2 import PdfMerger
import io


def generate_pdf_view(request, pk):
    obj = Order.objects.get(pk=pk)

    data = {
        "id": str(obj.id).zfill(10),
        "order_time": obj.created_at,
        "agent": f"{obj.agent.first_name} {obj.agent.last_name}",
        "agent_number": str(obj.agent.phone if obj.agent.phone else ""),
        "client": f"{obj.user.first_name} {obj.user.last_name}",
        "payment_type": obj.get_payment_type_display(),
        "address": obj.user.territory.first().name,
        "phone": str(obj.user.phone if obj.user.phone else ""),
        "items": obj.items.all(),
    }

    # Render the HTML template with context data
    html_string = render_to_string('contract.html', {'data': data})

    # Convert HTML to PDF
    pdf_file = HTML(string=html_string).write_pdf(stylesheets=[CSS(string='@page { size: A4 portrait; }')])

    # Create an HTTP response with PDF content
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="object_{obj.id}.pdf"'
    return response


def generate_pdf2_view(request):
    orders = request.GET.get("orders").split(",")
    orders = Order.objects.filter(pk__in=orders)
    users = ""
    total_sum = 0
    total_qty = 0
    items = []
    inserted_items = []

    for order in orders:
        users += order.user.get_full_name() + ", "
        for item in order.items.all():
            total_sum += float(item.qty) * float(item.price_uzs)
            total_qty += float(item.qty)

            if item.product_id not in inserted_items:

                items.append(
                    {
                        "id": item.product_id,
                        "title": item.product_name,
                        "product_in_set": float(item.product_in_set),
                        "set_amount": float(item.set_amount),
                        "qty": float(item.qty),
                        "price_uzs": float(item.qty) * float(item.price_uzs)
                    },

                )
                inserted_items.append(item.product_id)
            else:
                old_item = next((i for i in items if i["id"] == item.product_id), None)
                new_item = {
                    "id": item.product_id,
                    "title": old_item.get("title"),
                    "product_in_set": old_item.get("product_in_set"),
                    "set_amount": old_item.get("set_amount") + float(item.set_amount),
                    "qty": old_item.get('qty') + float(item.qty),
                    "price_uzs": old_item.get("price_uzs") + (float(item.qty) * float(item.price_uzs))
                }
                items.append(new_item)
                items.remove(old_item)
            selected_item = next((i for i in items if i["id"] == item.product_id), None)
            nabor = selected_item['qty'] - int(selected_item["set_amount"] * selected_item["product_in_set"])
            selected_item["case"] = nabor

    data = {
        "users": users,
        "total_qty": total_qty,
        "total_sum": total_sum,
        "items": items,
    }

    # Render the HTML template with context data
    html_string = render_to_string('contract2.html', {'data': data})

    # Convert HTML to PDF
    pdf_file = HTML(string=html_string).write_pdf(stylesheets=[CSS(string='@page { size: A4 portrait; }')])

    # Create an HTTP response with PDF content
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{users}.pdf"'
    return response


def generate_multiple_pdfs_view(request):
    ids = request.GET.get('ids').split(',')
    merger = PdfMerger()

    for pk in ids:
        obj = Order.objects.get(pk=pk)
        data = {
            "id": str(obj.id).zfill(10),
            "order_time": obj.created_at,
            "agent": f"{obj.agent.get_full_name() if obj.agent else 'net agenta'}",
            "agent_number": str(obj.agent.phone if obj.agent and obj.agent.phone else ""),
            "client": f"{obj.user.get_full_name() if obj.user else 'net klient'}",
            "payment_type": obj.get_payment_type_display(),
            "address": obj.user.territory.first().name if obj.user and obj.user.territory else "net territori",
            "phone": str(obj.user.phone if obj.user and obj.user.phone else ""),
            "items": obj.items.all(),
        }

        # Render the HTML template with context data
        html_string = render_to_string('contract.html', {'data': data})

        # Convert HTML to PDF as bytes
        pdf_bytes = HTML(string=html_string).write_pdf(stylesheets=[CSS(string='@page { size: A4 portrait; }')])

        # Wrap the bytes into a BytesIO object so that PdfMerger can read it
        pdf_file = io.BytesIO(pdf_bytes)

        # Append the in-memory PDF file to the merger
        merger.append(pdf_file)

    # Create a final response object to hold the merged PDF
    output_pdf = io.BytesIO()
    merger.write(output_pdf)
    merger.close()

    # Create an HTTP response with the merged PDF content
    response = HttpResponse(output_pdf.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="merged_orders.pdf"'

    return response
