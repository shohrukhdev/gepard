from django.urls import path
from . import views

urlpatterns = [
    path('nomenclature/update', views.NomenclatureUpdateView.as_view(), name='nomenclature_update'),
    path('contr_agents/update', views.CounterpartyUpdateView.as_view(), name='counterparty_update'),
    path('contr_agents/balances', views.CounterpartyBalanceView.as_view(), name='counterparty_balances'),
]