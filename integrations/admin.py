import json
import logging

from django.contrib import admin, messages
from django.utils import timezone

from integrations.models import Nomenclature, ContrAgent, ContrAgentBalance, Product
from integrations.utils.supply_send_request import prepare_order_data_from_nomenclature, create_order

logger = logging.getLogger(__name__)


class ProductInline(admin.TabularInline):
    model = Product
    extra = 0  # No extra empty forms
    readonly_fields = ['code', 'catalog_code', 'barcode', 'package_code', 'code1c', 'name']
    can_delete = False  # Prevent deletion of existing products
    max_num = 0  # Prevent adding new products

    def has_add_permission(self, request, obj=None):
        return False  # Another way to prevent adding new products


@admin.register(Nomenclature)
class NomenclatureAdmin(admin.ModelAdmin):
    list_display = ['external_id', 'client_name', 'date', 'created_at', 'sent_successfully']
    list_filter = ['sent_successfully', 'date', 'created_at']
    search_fields = ['external_id', 'client_name', 'customer_tin']
    readonly_fields = ['external_id', 'client_name', 'customer_tin', 'client_id', 'date', 'sent_on', 'created_at', 'response', 'sent_successfully']
    inlines = [ProductInline]
    actions = ['send_to_supply']

    fieldsets = (
        ('Basic Information', {
            'fields': ('external_id', 'client_id', 'client_name', 'customer_tin', 'date')
        }),
        ('Contract Information', {
            'fields': ('contract',)
        }),
        ('Status Information', {
            'fields': ('created_at', 'sent_on', 'sent_successfully', 'response')
        }),
    )

    def validate_nomenclature_for_sending(self, nomenclature):
        """
        Validates if the nomenclature and its products have all required fields filled.
        Returns a tuple of (is_valid, error_message)
        """
        missing_fields = []

        # Validate nomenclature fields
        required_fields = ['external_id', 'client_id', 'client_name', 'customer_tin', 'date']
        for field in required_fields:
            if not getattr(nomenclature, field):
                missing_fields.append(f"Nomenclature field '{field}' is missing")

        # Validate contract data
        try:
            contract_data = json.loads(nomenclature.contract) if nomenclature.contract else None
            if not contract_data:
                missing_fields.append("Contract information is missing")
        except json.JSONDecodeError:
            missing_fields.append("Contract information is not in valid JSON format")

        # Validate products
        products = nomenclature.products.all()
        if not products:
            missing_fields.append("No products associated with this nomenclature")

        for product in products:
            product_missing = []
            if not product.code:
                product_missing.append("code")
            if not product.name:
                product_missing.append("name")
            if product.count is None:
                product_missing.append("count")

            if product_missing:
                missing_fields.append(f"Product {product.id}: Missing fields: {', '.join(product_missing)}")

        is_valid = len(missing_fields) == 0
        error_message = "\n".join(missing_fields) if missing_fields else ""

        return is_valid, error_message

    def send_to_supply(self, request, queryset):
        """
        Admin action to send selected nomenclatures to supply service.
        Only processes nomenclatures that haven't been successfully sent yet.
        """
        success_count = 0
        error_count = 0

        for nomenclature in queryset:
            # Skip already successfully sent nomenclatures
            if nomenclature.sent_successfully:
                self.message_user(
                    request,
                    f"Nomenclature {nomenclature.external_id} already sent successfully. Skipping.",
                    messages.WARNING
                )
                continue

            # Validate nomenclature before sending
            is_valid, error_message = self.validate_nomenclature_for_sending(nomenclature)
            if not is_valid:
                self.message_user(
                    request,
                    f"Cannot send Nomenclature {nomenclature.external_id}: {error_message}",
                    messages.ERROR
                )
                error_count += 1
                continue

            try:
                # Prepare order data from nomenclature
                order_data = prepare_order_data_from_nomenclature(nomenclature)

                # Send the order to supply
                response = create_order(order_data)

                # Update nomenclature with response information
                nomenclature.sent_on = timezone.now()
                nomenclature.response = json.dumps(response)

                if response.get('success'):
                    nomenclature.sent_successfully = True
                    success_count += 1
                    message_level = messages.SUCCESS
                    message = f"Successfully sent Nomenclature {nomenclature.external_id} to supply."
                else:
                    error_count += 1
                    message_level = messages.ERROR
                    message = f"Failed to send Nomenclature {nomenclature.external_id}: {response.get('error', 'Unknown error')}"

                # Save the updated nomenclature
                nomenclature.save()
                self.message_user(request, message, message_level)

            except Exception as e:
                error_count += 1
                logger.exception(f"Error sending Nomenclature {nomenclature.external_id} to supply: {str(e)}")
                nomenclature.sent_on = timezone.now()
                nomenclature.response = json.dumps({"error": str(e)})
                nomenclature.save()
                self.message_user(
                    request,
                    f"Error sending Nomenclature {nomenclature.external_id}: {str(e)}",
                    messages.ERROR
                )

        if success_count > 0 or error_count > 0:
            self.message_user(
                request,
                f"Processing complete: {success_count} successfully sent, {error_count} failed.",
                messages.INFO
            )

    send_to_supply.short_description = "Send selected nomenclatures to supply"


@admin.register(ContrAgent)
class ContrAgentAdmin(admin.ModelAdmin):
    list_display = ['name', 'tin', 'cr_on', 'created_at']
    search_fields = ['name', 'tin']


@admin.register(ContrAgentBalance)
class Admin(admin.ModelAdmin):
    list_display = ['contr_agent', 'prepayment', 'debt', 'updated_at']
    list_filter = ['updated_at']
    search_fields = ['contr_agent__name', 'contr_agent__tin']

