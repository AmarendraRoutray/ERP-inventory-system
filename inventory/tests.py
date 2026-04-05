from django.test import TestCase

# Create your tests here.
from django.contrib.auth.models import User
from .models import *


class TransferTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="user", password="1234")
        self.admin = User.objects.create_user(username="admin", password="1234", is_staff=True)

        self.branch1 = Branch.objects.create(name="A", location="X")
        self.branch2 = Branch.objects.create(name="B", location="Y")

        self.product = Product.objects.create(name="Laptop", sku="LP1")

        self.stock = Stock.objects.create(
            product=self.product,
            branch=self.branch1,
            quantity=10
        )

    def test_successful_transfer(self):
        transfer = StockTransfer.objects.create(
            product=self.product,
            source_branch=self.branch1,
            destination_branch=self.branch2,
            quantity=5,
            created_by=self.user
        )

        from .views import ApproveTransferView
        view = ApproveTransferView()

        request = type("Request", (), {"user": self.admin})()

        view.post(request, transfer.id)

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, 5)

    def test_insufficient_stock(self):
        transfer = StockTransfer.objects.create(
            product=self.product,
            source_branch=self.branch1,
            destination_branch=self.branch2,
            quantity=20,
            created_by=self.user
        )

        from .views import ApproveTransferView
        view = ApproveTransferView()

        request = type("Request", (), {"user": self.admin})()

        response = view.post(request, transfer.id)

        self.assertEqual(response.status_code, 400)

    def test_permission_denied(self):
        transfer = StockTransfer.objects.create(
            product=self.product,
            source_branch=self.branch1,
            destination_branch=self.branch2,
            quantity=5,
            created_by=self.user
        )

        from .views import ApproveTransferView
        view = ApproveTransferView()

        request = type("Request", (), {"user": self.user})()

        response = view.post(request, transfer.id)

        self.assertEqual(response.status_code, 403)

    def test_duplicate_approval(self):
        transfer = StockTransfer.objects.create(
            product=self.product,
            source_branch=self.branch1,
            destination_branch=self.branch2,
            quantity=5,
            created_by=self.user,
            status="approved"
        )

        from .views import ApproveTransferView
        view = ApproveTransferView()

        request = type("Request", (), {"user": self.admin})()

        response = view.post(request, transfer.id)

        self.assertEqual(response.status_code, 400)

    def test_stock_summary(self):
        stocks = Stock.objects.filter(branch=self.branch1)
        self.assertEqual(stocks.count(), 1)