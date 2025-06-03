from django.urls import path
from .views import NomenclatureUpdateView, ContrAgentUpdateView, ContrAgentBalanceView

urlpatterns = [
    path('nomenclature/update/', NomenclatureUpdateView.as_view(), name='nomenclature-update'),
    path('contr_agents/update/', ContrAgentUpdateView.as_view(), name='contragent-update'),
    path('contr_agents/balances/', ContrAgentBalanceView.as_view(), name='contragent-balance'),
]

