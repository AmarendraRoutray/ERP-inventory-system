from django.shortcuts import render

# Create your views here.

from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import Branch, Product, Stock, StockTransfer, StockTransferLog
from .serializers import (
    BranchStockSummarySerializer,
    ProductSerializer,
    StockSerializer,
    StockTransferSerializer,
    UserSerializer,
    BranchSerializer,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db import transaction


class CreateUserView(APIView):

    def post(self, request):
        try:
            data = request.data
            username = data.get("username")
            password = data.get("password")
            is_staff = data.get("is_staff", False)

            if not all([username, password]):
                return Response(
                    {"error": "Username and password are required"}, status=400
                )

            if User.objects.filter(username=username).exists():
                return Response({"error": "Username already exists"}, status=400)

            instance = User.objects.create_user(username=username, password=password)
            instance.is_staff = is_staff
            instance.save()

            response = {
                "message": "User created successfully",
                "user": UserSerializer(instance).data,
            }
            return Response(response, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class BranchView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BranchSerializer

    def post(self, request):
        try:
            data = request.data
            name = data.get("name")
            location = data.get("location")

            if not all([name, location]):
                return Response({"error": "Name and location are required"}, status=400)

            if Branch.objects.filter(name=name).exists():
                return Response(
                    {"error": "Branch with this name already exists"}, status=400
                )

            instance = Branch.objects.create(name=name, location=location)

            response = {
                "message": "Branch created successfully",
                "data": BranchSerializer(instance).data,
            }
            return Response(response, status=201)

        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def get(self, request):
        try:
            queryset = Branch.objects.all().order_by("-created_at")
            paginator = PageNumberPagination()
            paginator.page_size = 10
            paginated_qs = paginator.paginate_queryset(queryset, request)
            serializer = BranchSerializer(paginated_qs, many=True)

            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response({"error": str(e)}, status=500)


class ProductView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer

    def post(self, request):
        try:
            data = request.data
            name = data.get("name")
            sku = data.get("sku")

            if not all([name, sku]):
                return Response({"error": "Name and SKU are required"}, status=400)

            if Product.objects.filter(sku=sku).exists():
                return Response(
                    {"error": "Product with this SKU already exists"}, status=400
                )

            instance = Product.objects.create(name=name, sku=sku)
            response = {
                "message": "Product created successfully",
                "data": ProductSerializer(instance).data,
            }
            return Response(response, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def get(self, request):
        try:
            queryset = Product.objects.all().order_by("-created_at")

            name = request.query_params.get("name")
            if name:
                queryset = queryset.filter(name__icontains=name)

            paginator = PageNumberPagination()
            paginator.page_size = 10
            paginated_qs = paginator.paginate_queryset(queryset, request)
            serializer = ProductSerializer(paginated_qs, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response({"error": str(e)}, status=500)


class StockView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            data = request.data
            product_id = data.get("product", None)
            branch_id = data.get("branch", None)
            quantity = data.get("quantity", 0)

            if not all([product_id, branch_id]):
                return Response(
                    {"error": "Product and branch are required"}, status=400
                )

            if quantity in [None, ""]:
                return Response({"error": "Quantity is required"}, status=400)

            try:
                quantity = int(quantity)
                if quantity < 0:
                    return Response(
                        {"error": "Quantity cannot be negative"}, status=400
                    )
            except (ValueError, TypeError):
                return Response(
                    {"error": "Quantity must be a valid number"}, status=400
                )

            try:
                product = Product.objects.get(id=product_id)
                branch = Branch.objects.get(id=branch_id)
            except Product.DoesNotExist:
                return Response({"error": "Invalid product"}, status=400)
            except Branch.DoesNotExist:
                return Response({"error": "Invalid branch"}, status=400)

            with transaction.atomic():
                stock, created = Stock.objects.select_for_update().get_or_create(
                    product=product, branch=branch, defaults={"quantity": 0}
                )
                stock.quantity = quantity
                stock.save()

            response = {
                "message": "Stock updated successfully",
                "data": StockSerializer(stock).data,
            }
            return Response(response, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)


class StockSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, branch_id):
        try:
            branch = Branch.objects.filter(id=branch_id).first()
            if not branch:
                return Response({"error": "Branch not found"}, status=404)

            serializer = BranchStockSummarySerializer(branch)

            return Response(serializer.data)

        except Exception as e:
            return Response({"error": str(e)}, status=500)


class StockTransferView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StockTransferSerializer

    def get(self, request):
        try:
            queryset = (
                StockTransfer.objects.all()
                .select_related("product", "source_branch", "destination_branch")
                .order_by("-created_at")
            )
            paginator = PageNumberPagination()
            page = paginator.paginate_queryset(queryset, request)
            serializer = self.serializer_class(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def post(self, request):
        try:
            data = request.data
            product_id = data.get("product")
            source_branch_id = data.get("source_branch")
            destination_branch_id = data.get("destination_branch")
            quantity = data.get("quantity")

            if not all([product_id, source_branch_id, destination_branch_id]):
                return Response({"error": "All fields are required"}, status=400)

            if source_branch_id == destination_branch_id:
                return Response(
                    {"error": "Source and destination cannot be same"}, status=400
                )

            if quantity in [None, ""]:
                return Response({"error": "Quantity is required"}, status=400)

            try:
                quantity = int(quantity)
                if quantity <= 0:
                    return Response(
                        {"error": "Quantity must be greater than 0"}, status=400
                    )
            except (ValueError, TypeError):
                return Response(
                    {"error": "Quantity must be a valid number"}, status=400
                )

            try:
                product = Product.objects.get(id=product_id)
                source_branch = Branch.objects.get(id=source_branch_id)
                destination_branch = Branch.objects.get(id=destination_branch_id)
            except Product.DoesNotExist:
                return Response({"error": "Invalid product"}, status=400)
            except Branch.DoesNotExist:
                return Response({"error": "Invalid branch"}, status=400)

            # checking product and branch status
            if not product.is_active:
                return Response({"error": "Product is inactive"}, status=400)

            if not source_branch.is_active or not destination_branch.is_active:
                return Response(
                    {"error": "One of the branches is inactive"}, status=400
                )

            # checking stock availability in source branch
            stock = Stock.objects.filter(product=product, branch=source_branch).first()
            if not stock:
                return Response(
                    {"error": "Stock not found in source branch"}, status=400
                )

            if stock.quantity < quantity:
                return Response({"error": "Insufficient stock"}, status=400)

            with transaction.atomic():
                transfer = StockTransfer.objects.create(
                    product=product,
                    source_branch=source_branch,
                    destination_branch=destination_branch,
                    quantity=quantity,
                    created_by=request.user,
                )
                StockTransferLog.objects.create(
                    transfer=transfer,
                    action="created",
                    performed_by=request.user,
                    message="Transfer request created",
                )
            return Response(
                {
                    "message": "Stock transfer created successfully",
                    "data": self.serializer_class(transfer).data,
                },
                status=200,
            )

        except Exception as e:
            return Response({"error": str(e)}, status=500)


class ApproveTransferView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, transfer_id):
        try:
            if not request.user.is_staff:
                return Response({"error": "Only staff can approve"}, status=403)

            with transaction.atomic():
                transfer = StockTransfer.objects.select_for_update().get(id=transfer_id)

                if transfer.status != "pending":
                    return Response({"error": "Transfer already processed"}, status=400)

                # locking stock rows
                source_stock = Stock.objects.select_for_update().get(
                    product=transfer.product, branch=transfer.source_branch
                )

                if source_stock.quantity < transfer.quantity:
                    transfer.status = "failed"
                    transfer.save()

                    StockTransferLog.objects.create(
                        transfer=transfer,
                        action="failed",
                        performed_by=request.user,
                        message="Insufficient stock",
                    )

                    return Response({"error": "Insufficient stock"}, status=400)

                destination_stock, _ = Stock.objects.select_for_update().get_or_create(
                    product=transfer.product,
                    branch=transfer.destination_branch,
                    defaults={"quantity": 0},
                )

                # updating stock quantities
                source_stock.quantity -= transfer.quantity
                destination_stock.quantity += transfer.quantity

                source_stock.save()
                destination_stock.save()

                transfer.status = "approved"
                transfer.save()

                # Audit log
                StockTransferLog.objects.create(
                    transfer=transfer,
                    action="approved",
                    performed_by=request.user,
                    message="Transfer completed successfully",
                )

            return Response({"message": "Transfer approved successfully"})

        except StockTransfer.DoesNotExist:
            return Response({"error": "Transfer not found"}, status=400)

        except Exception as e:
            return Response({"error": str(e)}, status=500)
