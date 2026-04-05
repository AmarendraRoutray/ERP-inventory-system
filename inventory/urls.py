from django.urls import path
from .views import ApproveTransferView, BranchView, StockTransferView, CreateUserView, ProductView, StockSummaryView, StockView

urlpatterns = [
    path('create-user', CreateUserView.as_view() ),
    path('branch', BranchView.as_view() ),
    path('product', ProductView.as_view()),
    path('stock', StockView.as_view()),
    path('branches/<str:branch_id>/stock-summary/', StockSummaryView.as_view()),
    path('transfers/', StockTransferView.as_view()),
    path('transfers/<str:transfer_id>/approve/', ApproveTransferView.as_view()),
]
