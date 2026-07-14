from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline
from .models import (
    ProductCategory, Product, ProductImage, Cart, CartItem,
    Order, OrderItem, Wishlist, ProductReview,
)


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['line_total']


@admin.register(ProductCategory)
class ProductCategoryAdmin(ModelAdmin):
    list_display = ['name', 'slug', 'sort_order', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['sort_order', 'name']


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ['name', 'category', 'seller', 'price', 'stock', 'is_active', 'is_featured', 'rating', 'sales_count']
    list_filter = ['category', 'is_active', 'is_featured', 'pet_type', 'created_at']
    list_editable = ['is_active', 'is_featured', 'stock', 'price']
    search_fields = ['name', 'slug', 'seller__store_name']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['id', 'rating', 'review_count', 'sales_count', 'views_count', 'created_at', 'updated_at']
    autocomplete_fields = ['category', 'seller']
    inlines = [ProductImageInline]
    ordering = ['-created_at']

    fieldsets = (
        (_('Product'), {'fields': ('seller', 'category', 'name', 'slug', 'description', 'pet_type')}),
        (_('Pricing & Stock'), {'fields': ('price', 'stock', 'is_active', 'is_featured')}),
        (_('Stats'), {'fields': ('rating', 'review_count', 'sales_count', 'views_count')}),
        (_('Metadata'), {'fields': ('id', 'created_at', 'updated_at')}),
    )


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ['id', 'user', 'seller', 'status', 'payment_method', 'total', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    list_editable = ['status']
    search_fields = ['user__email', 'user__full_name', 'stripe_session_id']
    readonly_fields = ['id', 'subtotal', 'shipping_fee', 'tax', 'total', 'created_at', 'updated_at']
    autocomplete_fields = ['user', 'seller']
    inlines = [OrderItemInline]
    ordering = ['-created_at']

    fieldsets = (
        (_('Order'), {'fields': ('user', 'seller', 'status', 'payment_method')}),
        (_('Amounts'), {'fields': ('subtotal', 'shipping_fee', 'tax', 'total')}),
        (_('Shipping'), {'fields': ('shipping_address', 'stripe_session_id')}),
        (_('Metadata'), {'fields': ('id', 'created_at', 'updated_at')}),
    )


@admin.register(Cart)
class CartAdmin(ModelAdmin):
    list_display = ['user', 'created_at']
    search_fields = ['user__email']


@admin.register(CartItem)
class CartItemAdmin(ModelAdmin):
    list_display = ['cart', 'product', 'quantity']
    list_filter = ['created_at']


@admin.register(OrderItem)
class OrderItemAdmin(ModelAdmin):
    list_display = ['order', 'product_name', 'price', 'quantity', 'line_total']
    search_fields = ['product_name', 'order__id']


@admin.register(Wishlist)
class WishlistAdmin(ModelAdmin):
    list_display = ['user', 'product', 'created_at']
    search_fields = ['user__email', 'product__name']


@admin.register(ProductReview)
class ProductReviewAdmin(ModelAdmin):
    list_display = ['product', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['product__name', 'user__email', 'comment']
    readonly_fields = ['id', 'created_at', 'updated_at']
