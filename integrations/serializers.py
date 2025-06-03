from rest_framework import serializers
from .models import ContrAgent, ContrAgentBalance, Nomenclature, Product


class ContrAgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContrAgent
        fields = ['name', 'tin', 'cr_on']
        read_only_fields = ['cr_on']


class ContrAgentBalanceSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='contr_agent.name', read_only=True)
    tin = serializers.CharField(source='contr_agent.tin', read_only=True)

    class Meta:
        model = ContrAgentBalance
        fields = ['name', 'tin', 'prepayment', 'debt', 'updated_at', 'last_sync_timestamp']
        read_only_fields = ['updated_at', 'last_sync_timestamp']


class ProductSerializer(serializers.ModelSerializer):
    code1C = serializers.CharField(source='code1c', required=False, allow_null=True)

    class Meta:
        model = Product
        fields = ['code', 'catalog_code', 'barcode', 'package_code', 'code1C', 'name']


class NomenclatureSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)

    class Meta:
        model = Nomenclature
        fields = ['nomenclatura_id_1c', 'client_id', 'client_name',
                  'customer_tin', 'contract', 'date', 'products']