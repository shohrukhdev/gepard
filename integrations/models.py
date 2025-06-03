from django.db import models


class Nomenclature(models.Model):
    """"
    Nomenclature object received from 1C service.
    """
    external_id = models.CharField(max_length=64)
    client_id = models.CharField(max_length=64, null=True, blank=True)
    client_name = models.CharField(max_length=128, null=True, blank=True)
    customer_tin = models.CharField(max_length=20, null=True, blank=True)
    contract = models.TextField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_on = models.DateTimeField(null=True, blank=True)
    response = models.TextField(null=True, blank=True)
    sent_successfully = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Nomenclature"
        verbose_name_plural = "Nomenclatures"
        ordering = ['-created_at']

    def __str__(self):
        return f"Nomenclature {self.external_id} - {self.client_name or 'No client'}"


class Product(models.Model):
    """
    Product comes inside Nomenclature object from 1C.
    """
    nomenclature = models.ForeignKey(
        Nomenclature,
        on_delete=models.CASCADE,
        related_name="products"
    )
    code = models.CharField(max_length=32, null=True, blank=True)
    catalog_code = models.CharField(max_length=32, null=True, blank=True)
    barcode = models.CharField(max_length=128, null=True, blank=True)
    package_code = models.CharField(max_length=32, null=True, blank=True)
    code1c = models.CharField(max_length=32, null=True, blank=True)
    name = models.CharField(max_length=256, null=True, blank=True)

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['name']

    def __str__(self):
        return self.name or f"Product {self.id}"


class ContrAgent(models.Model):
    """
    Contracting Agent received from 1C service.
    """
    name = models.CharField(max_length=256)
    tin = models.CharField(max_length=20, unique=True)
    cr_on = models.DateTimeField(auto_now=True)  # Updates whenever the record is updated
    created_at = models.DateTimeField(auto_now_add=True)  # When the record was first created

    class Meta:
        verbose_name = "ContrAgent"
        verbose_name_plural = "ContrAgents"
        ordering = ['-cr_on']
        indexes = [
            models.Index(fields=['tin']),
        ]

    def __str__(self):
        return f"{self.name} (TIN: {self.tin})"


class ContrAgentBalance(models.Model):
    """
    Balance information for a Contracting Agent.
    """
    contr_agent = models.OneToOneField(
        ContrAgent,
        on_delete=models.CASCADE,
        related_name="balance"
    )
    prepayment = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    debt = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)
    last_sync_timestamp = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "ContrAgent Balance"
        verbose_name_plural = "ContrAgent Balances"
        ordering = ['-updated_at']

    def __str__(self):
        return f"Balance for {self.contr_agent.name} - Prepayment: {self.prepayment}, Debt: {self.debt}"
