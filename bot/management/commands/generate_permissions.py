from bot.models import TelegramUser, CustomUser, Product, Order, OrderItem, Contact
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    help = 'Creates a permission group with permissions for multiple models'

    def handle(self, *args, **kwargs):
        group_name = "default"

        # List of models to include in the group
        models = [TelegramUser, CustomUser, Product, Order, OrderItem, Contact]

        # Check if the group already exists
        if not Group.objects.filter(name=group_name).exists():
            # Create the group
            group = Group.objects.create(name=group_name)
            self.stdout.write(self.style.SUCCESS(f'Group "{group_name}" created.'))

            # Add permissions for each model to the group
            for model in models:
                content_type = ContentType.objects.get_for_model(model)
                permissions = Permission.objects.filter(content_type=content_type)

                for permission in permissions:
                    group.permissions.add(permission)
                    self.stdout.write(self.style.SUCCESS(f'Added permission "{permission.codename}" to group "{group_name}".'))

            self.stdout.write(self.style.SUCCESS(f'Group "{group_name}" with permissions for multiple models created successfully.'))

        if not Group.objects.filter(name="keeper").exists():
            group = Group.objects.create(name="keeper")
            models = [Order, OrderItem]

            for model in models:
                content_type = ContentType.objects.get_for_model(model)
                permissions = Permission.objects.filter(content_type=content_type)

                for permission in permissions:
                    group.permissions.add(permission)
                    self.stdout.write(self.style.SUCCESS(f'Added permission "{permission.codename}" to group "{group_name}".'))

