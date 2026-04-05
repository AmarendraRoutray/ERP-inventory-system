from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Branch, Product, Product, Stock, StockTransfer


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "is_staff"]


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"


class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = "__all__"


class StockSummaryItemSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return {
            "id": instance.product.id,
            "name": instance.product.name,
            "sku": instance.product.sku,
            "quantity": instance.quantity,
        }

    class Meta:
        model = Stock
        fields = ["quantity"]


class BranchStockSummarySerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()
    class Meta:
        model = Branch
        fields = ["products"]

    def to_representation(self, instance):
        return {
            "branch": {
                "id": instance.id,
                "name": instance.name,
                "location": instance.location,
                "is_active": instance.is_active,
            },
            "products": self.get_products(instance),
        }

    def get_products(self, obj):
        stocks = obj.stock_set.all().select_related("product")
        return StockSummaryItemSerializer(stocks, many=True).data


class StockTransferSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return {
            "id": instance.id,
            "product": {
                "id": instance.product.id,
                "name": instance.product.name,
                "sku": instance.product.sku,
            },
            "source_branch": {
                "id": instance.source_branch.id,
                "name": instance.source_branch.name,
                "location": instance.source_branch.location,
            },
            "destination_branch": {
                "id": instance.destination_branch.id,
                "name": instance.destination_branch.name,
                "location": instance.destination_branch.location,
            },
            "quantity": instance.quantity,
            "status": instance.status,
            "created_by": {
                "id": instance.created_by.id,
                "username": instance.created_by.username,
            },
            "reference_id": instance.reference_id,
        }
    class Meta:
        model = StockTransfer
        fields = '__all__'
        read_only_fields = ['status', 'created_by', 'reference_id']