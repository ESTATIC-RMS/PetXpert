from django.urls import path
from . import views

urlpatterns = [
    path('categories/', views.CategoryListView.as_view()),
    path('products/', views.ProductListView.as_view()),
    path('products/<uuid:product_id>/', views.ProductDetailView.as_view()),
    path('products/<uuid:product_id>/review/', views.ProductReviewView.as_view()),
    path('cart/', views.CartView.as_view()),
    path('checkout/', views.CheckoutView.as_view()),
    path('orders/', views.OrderListView.as_view()),
    path('wishlist/', views.WishlistView.as_view()),
    path('seller/products/', views.SellerProductListView.as_view()),
    path('seller/orders/', views.SellerOrderListView.as_view()),
    path('seller/orders/<uuid:order_id>/', views.SellerOrderUpdateView.as_view()),
    path('seller/sales-summary/', views.SellerSalesSummaryView.as_view()),
    path('seller/inventory-stats/', views.SellerInventoryStatsView.as_view()),
]
