from django.db import models


class Nomenclature(models.Model):
    """"
    Nomenclature object received from 1C service.
    """
    external_id = models.CharField(max_length=64, verbose_name="ID из 1С")
    client_id = models.CharField(max_length=64, null=True, blank=True, verbose_name="ID клиента")
    client_name = models.CharField(max_length=128, null=True, blank=True, verbose_name="Название клиента")
    customer_tin = models.CharField(max_length=20, null=True, blank=True, verbose_name="ИНН клиента")
    contract = models.TextField(null=True, blank=True, verbose_name="Контракт")
    date = models.DateField(null=True, blank=True, verbose_name="Дата")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    sent_on = models.DateTimeField(null=True, blank=True, verbose_name="Отправлено")
    response = models.TextField(null=True, blank=True, verbose_name="Ответ от Supply")
    sent_successfully = models.BooleanField(default=False, verbose_name="Отправлено успешно")

    class Meta:
        verbose_name = "Номенклатура"
        verbose_name_plural = "Номенклатуры"
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
    code = models.CharField(max_length=32, null=True, blank=True, verbose_name="Код товара")
    catalog_code = models.CharField(max_length=32, null=True, blank=True, verbose_name="Код каталога")
    barcode = models.CharField(max_length=128, null=True, blank=True, verbose_name="Штрихкод")
    baseSumma = models.IntegerField(null=True, blank=True, verbose_name="Базовая сумма")
    package_code = models.CharField(max_length=32, null=True, blank=True, verbose_name="Код упаковки")
    count = models.IntegerField(null=True, blank=True, verbose_name="Количество")
    summa = models.IntegerField(null=True, blank=True, verbose_name="Сумма")
    delivery_sum = models.IntegerField(null=True, blank=True, verbose_name="Сумма доставки")
    code1c = models.CharField(max_length=32, null=True, blank=True, verbose_name="Код 1С")
    name = models.CharField(max_length=256, null=True, blank=True, verbose_name="Название")

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"
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
