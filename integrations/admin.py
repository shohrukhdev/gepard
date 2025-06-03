from django.contrib import admin

from integrations.models import Nomenclature, ContrAgent, ContrAgentBalance


@admin.register(Nomenclature)
class NomenclatureAdmin(admin.ModelAdmin):
    pass


@admin.register(ContrAgent)
class ContrAgentAdmin(admin.ModelAdmin):
    pass


@admin.register(ContrAgentBalance)
class Admin(admin.ModelAdmin):
    pass
