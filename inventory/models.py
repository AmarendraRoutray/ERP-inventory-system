from django.db import models

# Create your models here.

from django.contrib.auth.models import User
import uuid


def getId(prefix):
    return f"{prefix}{uuid.uuid4().hex[:8]}"


MODEL_ID_PREFIX = {
    "Branch": "brn_",
    "Product": "prd_",
    "Stock": "stk_",
    "StockTransfer": "trf_",
    "StockTransferLog": "log_",
}


def get_unique_model_id(model_class):
    model_name = model_class.__name__
    prefix = MODEL_ID_PREFIX.get(model_name)

    if not prefix:
        raise ValueError(f"No prefix defined for model: {model_name}")

    new_id = getId(prefix)
    while model_class.objects.filter(id=new_id).exists():
        new_id = getId(prefix)

    return new_id


class Branch(models.Model):
    id = models.CharField(primary_key=True, editable=False, max_length=50)
    name = models.CharField(max_length=255, unique=True)
    location = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = get_unique_model_id(Branch)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    id = models.CharField(primary_key=True, editable=False, max_length=50)
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = get_unique_model_id(Product)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.sku})"


class Stock(models.Model):
    id = models.CharField(primary_key=True, editable=False, max_length=50)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("product", "branch")
        indexes = [models.Index(fields=["product", "branch"])]

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = get_unique_model_id(Stock)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product} - {self.branch} ({self.quantity})"


class StockTransfer(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("failed", "Failed"),
    ]

    id = models.CharField(primary_key=True, editable=False, max_length=50)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    source_branch = models.ForeignKey(
        Branch, related_name="source_transfers", on_delete=models.CASCADE
    )
    destination_branch = models.ForeignKey(
        Branch, related_name="destination_transfers", on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    reference_id = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["product"]),
            models.Index(fields=["source_branch"]),
            models.Index(fields=["destination_branch"]),
        ]

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = get_unique_model_id(StockTransfer)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product} ({self.quantity})"


class StockTransferLog(models.Model):
    id = models.CharField(primary_key=True, editable=False, max_length=50)
    transfer = models.ForeignKey(StockTransfer, on_delete=models.CASCADE)
    action = models.CharField(max_length=50)  # created / approved / failed
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = get_unique_model_id(StockTransferLog)
        super().save(*args, **kwargs)
