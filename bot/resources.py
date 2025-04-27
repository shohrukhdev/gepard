from import_export import resources
from bot.models import TelegramUser, Order


class UsersTableResourse(resources.ModelResource):

    def dehydrate_is_agent(self, obj):
        if obj.is_agent:
            return "Да"
        return "Нет"
    
    def dehydrate_is_active(self, obj):
        if obj.is_active:
            return "Да"
        return "Нет"
    
    def dehydrate_category(self, obj):
        if obj.category:
            return obj.category.name
        return "Нет"
    
    def dehydrate_territory(self, obj):
        if obj.territory:
            return obj.territory.name
        return "Нет"
    
    class Meta:
        model = TelegramUser
        exclude = ("id", "telegram_id", "username", "is_updated")

    def get_export_headers(self, fields=None):
        return ['Имя', 'Фамилия', 'Агент', 'Активен', 'Номер телефона', 'ИНН', 'Категория', 'Территория']
        


class OrderResource(resources.ModelResource):
    def dehydrate_user(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}"
        return "-"
    
    def dehydrate_agent(self, obj):
        if obj.agent:
            return f"{obj.agent.first_name} {obj.agent.last_name}"
        return "-"
    
    def dehydrate_payment_status(self, obj):
        return obj.get_payment_status_display()
    
    def dehydrate_payment_type(self, obj):
        return obj.get_payment_type_display()
    
    def dehydrate_status(self, obj):
        return obj.get_status_display()
    
    def dehydrate_created_at(self, obj):
        return obj.created_at.strftime("%d.%m.%Y %H:%M:%S")

    def dehydrate_location_path(self, obj):
        if obj.location_path:
            return f'=HYPERLINK("{obj.location_path}", "Карта")'
        return '-'
    
    def dehydrate_accountant_approve_time(self, obj):
        if obj.accountant_approve_time:
            return obj.accountant_approve_time.strftime("%d.%m.%Y %H:%M:%S")
        return '-'
    
    def dehydrate_director_approve_time(self, obj):
        if obj.director_approve_time:
            return obj.director_approve_time.strftime("%d.%m.%Y %H:%M:%S")
        return '-'
    
    def dehydrate_storekeeper_approve_time(self, obj):
        if obj.storekeeper_approve_time:
            return obj.storekeeper_approve_time.strftime("%d.%m.%Y %H:%M:%S")
        return '-'
    
    def get_export_headers(self, fields=None):
        return ("Клиент", "Агент", "Статус платежа", "Тип платежа", "Статус заказа", 
                "Время размещения заказа", "Место доставки", "Бухгалтер", "Директор", "Кладовщик")
    

    class Meta:
        model = Order
        exclude = ("id", )
        