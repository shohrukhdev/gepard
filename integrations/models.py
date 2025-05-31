from django.db import models


class Nomenclature(models.Model):
    """"
    Nomenclature object received from 1C service.
    """
    external_id = models.CharField(max_length=64, name="nomenclatura_id_1c")
    client_id = models.CharField(max_length=64, null=True, blank=True)
    client_name = models.CharField(max_length=128, null=True, blank=True)
    customer_tin = models.CharField(max_length=20, null=True, blank=True)
    contract = models.TextField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Product(models.Model):
    """
    Product comes inside Nomenclature object from 1C.
    """
    nomenclature = models.ForeignKey(Nomenclature, related_name="nomenclature_product")
    code = models.CharField(max_length=32, null=True, blank=True)
    catalog_code = models.CharField(max_length=32, null=True, blank=True)
    barcode = models.CharField(max_length=128, null=True, blank=True)
    package_code = models.CharField(max_length=32, null=True, blank=True)
    code1c = models.CharField(max_length=32, null=True, blank=True)
    name = models.CharField(max_length=256, null=True, blank=True)



