from django.db import models
from solo.models import SingletonModel
from django.contrib.auth.models import AbstractUser, Group
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
from uuid import uuid4
from datetime import datetime


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('director', 'Директор'),
        ('accountant', 'Бухгалтер'),
        ('storekeeper', 'Заведующий складом'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    class Meta:
        verbose_name = "Менеджер"
        verbose_name_plural = "Менеджеры"

    def save(self, *args, **kwargs):
        call_command('generate_permissions')

        if not self.pk:
            self.password = make_password(self.password)
            self.is_active = True
            self.is_staff = True
            super().save(*args, **kwargs)

        if not self.is_superuser:
            if self.role == "director" or self.role == "accountant":
                groups = Group.objects.filter(name="default")
                self.groups.set(groups)
            else:
                groups = Group.objects.filter(name="keeper")
                self.groups.set(groups)

    def __str__(self):
        return self.username


class ClientCategory(models.Model):
    class ActionTypes(models.TextChoices):
        INCREASE = "increase", "Добавлять"
        DECREASE = "decrease", "Вычесть"

    name = models.CharField("Название", max_length=255)
    action = models.CharField("Добавить/вычесть цену", choices=ActionTypes.choices, default=ActionTypes.INCREASE,
                              max_length=255)
    amount_uzs = models.CharField("Сумма UZS", max_length=255)
    amount_usd = models.CharField("Сумма USD", max_length=255)

    class Meta:
        verbose_name = "Категория клиента"
        verbose_name_plural = "Категории клиентов"

    def __str__(self) -> str:
        return self.name


class TelegramUser(models.Model):
    class UserCategory(models.TextChoices):
        A = "a", "Стандарт"
        B = "b", "-4%"
        C = "c", "Хорека"
        D = "d", "Оптовик"
        E = "e", "-2%"

    telegram_id = models.CharField(unique=True, max_length=255)
    username = models.CharField(max_length=255, blank=True, null=True, editable=False)
    first_name = models.CharField("Названия клиента", max_length=255, blank=True, null=True)
    last_name = models.CharField("Фамилия", max_length=255, blank=True, null=True, editable=False)
    is_agent = models.BooleanField("Торговый представитель ?", default=False)
    contract_id = models.CharField("Номер договор", null=True, blank=True, max_length=255)
    is_active = models.BooleanField("Он активен?", default=True)
    phone = models.CharField("Номер телефона", null=True, blank=True, max_length=255)
    address = models.TextField("Адрес", null=True, blank=True)
    is_updated = models.BooleanField(editable=False, default=False)
    tin = models.CharField("ИНН", null=True, blank=True, max_length=255)
    limit = models.FloatField("Сумма лимит (UZS)", default=0)
    category = models.CharField(verbose_name="Категория клиента", null=True, blank=True, max_length=255,
                                choices=UserCategory.choices)
    territory = models.ManyToManyField("Area", verbose_name="Территория", null=True, blank=True)

    def clean(self) -> None:
        if not self.tin and not self.contract_id:
            raise ValidationError({
                "tin": "ИНН и номер договора обязательны.",
                "contract_id": "ИНН и номер договора обязательны."
            })

        return super().clean()

    def save(self, *args, **kwargs):
        if not self.telegram_id:
            self.telegram_id = uuid4()

        return super().save(*args, **kwargs)

    def get_full_name(self):
        first_name = self.first_name if self.first_name else ""
        last_name = self.last_name if self.last_name else ""

        return f"{first_name} {last_name}"

    def __str__(self) -> str:
        return self.get_full_name()

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"


class Contact(SingletonModel):
    body = models.TextField("Текст")

    class Meta:
        verbose_name = "Связаться с нами"
        verbose_name_plural = "Связаться с нами"


class Category(models.Model):
    cover = models.ImageField("Изображение категории", upload_to="categories")
    title = models.CharField("Название категории", max_length=255)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категория товаров"

    def __str__(self) -> str:
        return self.title


class Product(models.Model):
    cover = models.ImageField("Изображение продукта", upload_to="products")
    title = models.CharField("Название продукта", max_length=255)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        verbose_name="Категория"
    )
    description = models.TextField("Комментарий")
    is_active = models.BooleanField("Активен", default=True)
    price_uzs = models.FloatField("Цена (сум)", default=0, editable=False)
    price_usd = models.FloatField("Цена (долл. США)", default=0, editable=False)

    price_uzs_a = models.FloatField("Стандарт Цена (сум)", default=0)
    price_usd_a = models.FloatField("Стандарт Цена (долл. США)", default=0, editable=False)

    price_uzs_b = models.FloatField("-4% Цена (сум)", default=0)
    price_usd_b = models.FloatField("-4% Цена (долл. США)", default=0, editable=False)

    price_uzs_c = models.FloatField("Хорека Цена (сум)", default=0)
    price_usd_c = models.FloatField("Хорека Цена (долл. США)", default=0, editable=False)

    price_uzs_d = models.FloatField("Оптовик Цена (сум)", default=0)
    price_usd_d = models.FloatField("Оптовик Цена (долл. США)", default=0, editable=False)

    price_uzs_e = models.FloatField("-2% Цена (сум)", default=0)
    price_usd_e = models.FloatField("-2% Цена (долл. США)", default=0, editable=False)

    amount = models.FloatField("Количество", default=0)
    set_amount = models.FloatField("Количество в блоке", default=0)
    is_top = models.BooleanField("Популярный продукт", default=False)

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"

    def __str__(self) -> str:
        return self.title


class Order(models.Model):
    class PaymentTypes(models.TextChoices):
        CASH = "cash", "Наличные"
        PAYME = "payme", "Payme"
        CLICK = "click", "Click"
        TERMINAL = "terminal", "Терминал"
        TRANSFER = "transfer", "Перечисления"
        OTHER = "other", "Другой"

    class PaymentStatus(models.TextChoices):
        PAID = "paid", "Оплаченный"
        UNPAID = "unpaid", "Неоплачиваемый"

    class OrderStatus(models.TextChoices):
        PENDING = "pending", "Новый"
        APPROVED_BY_ACCOUNTANT = "approved_by_account", "Аттестовано бухгалтером"
        APPROVED_BY_DIRECTOR = "approved_by_director", "Утверждено директором"
        APPROVED_BY_STOREKEEPER = "approved_by_storekeeper", "Подтверждено кладовщиком"
        CANCELLED = "cancelled", "Отменено"

    class DirectorStatus(models.TextChoices):
        APPROVED_BY_ACCOUNTANT = "approved_by_account", "Аттестовано бухгалтером"
        APPROVED_BY_DIRECTOR = "approved_by_director", "Утверждено директором"
        CANCELLED = "cancelled", "Отменено"

    class AccountantStatus(models.TextChoices):
        PENDING = "pending", "Yangi"
        APPROVED_BY_ACCOUNTANT = "approved_by_account", "Аттестовано бухгалтером"
        CANCELLED = "cancelled", "Отменено"

    class StoreKeeperStatus(models.TextChoices):
        APPROVED_BY_DIRECTOR = "approved_by_director", "Утверждено директором"
        APPROVED_BY_STOREKEEPER = "approved_by_storekeeper", "Подтверждено кладовщиком"

    user = models.ForeignKey(verbose_name="Клиент", to=TelegramUser, on_delete=models.SET_NULL, null=True, blank=True)
    agent = models.ForeignKey(verbose_name="Agent", to=TelegramUser, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name="orders")
    payment_status = models.CharField("Статус платежа", choices=PaymentStatus.choices, default=PaymentStatus.UNPAID,
                                      max_length=16)
    payment_type = models.CharField("Тип платежа", choices=PaymentTypes.choices, null=True, blank=True, max_length=16)
    status = models.CharField("Статус заказа", max_length=24, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    created_at = models.DateTimeField("Время размещения заказа", auto_now=True)
    location_path = models.URLField("Место доставки", null=True, blank=True)
    accountant_approve_time = models.DateTimeField("Время утверждения бухгалтером", null=True, blank=True)
    director_approve_time = models.DateTimeField("Время утверждения директором", null=True, blank=True)
    storekeeper_approve_time = models.DateTimeField("Время одобрения кладовщика", null=True, blank=True)
    comment = models.TextField("Комментарий", null=True, blank=True)
    is_accountant_confirm = models.BooleanField("Бухгалтер подтвердил?", default=False)
    is_director_confirm = models.BooleanField("Директор подтвердил?", default=False)
    is_storekeeper_confirm = models.BooleanField("Кладовщик подтвердил?", default=False)

    def clean(self) -> None:
        from django.core.exceptions import ValidationError
        if self.payment_status == "paid" and not self.payment_type:
            raise ValidationError(
                {"payment_type": "При изменении статуса платежа на «Оплачен» необходимо указать тип платежа."})
        return super().clean()

    def save(self, *args, **kwargs):
        from bot.signals import make_order_message, send_notification
        if self.pk:
            message = None
            if self.is_accountant_confirm and not self.accountant_approve_time:
                self.accountant_approve_time = datetime.now()
                self.status = Order.OrderStatus.APPROVED_BY_ACCOUNTANT
                message = make_order_message(self, "accountant")
            elif self.is_director_confirm and not self.director_approve_time:
                self.director_approve_time = datetime.now()
                self.status = Order.OrderStatus.APPROVED_BY_DIRECTOR
                message = make_order_message(self, "director")
            elif self.is_storekeeper_confirm and not self.storekeeper_approve_time:
                self.storekeeper_approve_time = datetime.now()
                self.status = Order.OrderStatus.APPROVED_BY_STOREKEEPER
                message = make_order_message(self, "storekeeper")

            if self.agent and self.agent.telegram_id and message:
                send_notification(self.agent.telegram_id, message)

        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"


class OrderItem(models.Model):
    order = models.ForeignKey(verbose_name="Заказ", related_name="items", to=Order, on_delete=models.CASCADE)
    product_name = models.CharField("Название продукта", max_length=255)
    product_in_set = models.FloatField("Количество в Блок", default=0)
    product_id = models.IntegerField(default=0)
    qty = models.CharField("Количество", max_length=255)
    set_amount = models.CharField("Блок", max_length=255, default="0")
    price_uzs = models.CharField("Цена sum", max_length=255)
    price_usd = models.CharField("Цена USD", max_length=255, null=True, blank=True, editable=False)

    def get_real_qty(self):
        try:
            product = Product.objects.get(id=self.product_id)
            set_amount = int(product.amount) // int(product.set_amount)
            return f"{product.amount} dona"
        except:
            return f"0x0"

    get_real_qty.short_description = "Oстатка"

    class Meta:
        verbose_name = "Заказанные продукты"
        verbose_name_plural = "Заказанные продукты"


class Area(models.Model):
    name = models.CharField("Название", max_length=255)

    class Meta:
        verbose_name = "Территория"
        verbose_name_plural = "Территории"

    def __str__(self) -> str:
        return f"{self.pk}. {self.name}"
