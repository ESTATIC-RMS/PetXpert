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
    list_display = ['name', 'slug', 'sort_order', 'get_product_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['sort_order', 'name']
    readonly_fields = ['id', 'created_at', 'updated_at']

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True, is_deleted=False).count()
    get_product_count.short_description = 'Active Products'


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ['name', 'get_seller_info', 'category', 'price', 'stock', 'is_active', 'is_featured', 'rating', 'review_count', 'sales_count', 'views_count', 'created_at']
    list_filter = ['category', 'is_active', 'is_featured', 'pet_type', 'created_at']
    list_editable = ['is_active', 'is_featured', 'stock', 'price']
    search_fields = ['name', 'slug', 'seller__store_name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['id', 'rating', 'review_count', 'sales_count', 'views_count', 'created_at', 'updated_at']
    autocomplete_fields = ['category', 'seller']
    inlines = [ProductImageInline]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    fieldsets = (
        (_('Product Information'), {'fields': ('seller', 'category', 'name', 'slug', 'description', 'pet_type')}),
        (_('Pricing & Inventory'), {'fields': ('price', 'compare_at_price', 'stock', 'is_active', 'is_featured')}),
        (_('Performance Statistics'), {'fields': ('rating', 'review_count', 'sales_count', 'views_count')}),
        (_('Metadata'), {'fields': ('id', 'created_at', 'updated_at')}),
    )

    def get_seller_info(self, obj):
        if obj.seller:
            return f"{obj.seller.store_name} ({'✓' if obj.seller.is_verified else '✗'})"
        return "No Seller"
    get_seller_info.short_description = 'Seller'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('seller', 'category')


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ['id', 'get_user_info', 'get_seller_info', 'status', 'payment_method', 'get_total', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    list_editable = ['status']
    search_fields = ['user__email', 'user__full_name', 'seller__store_name', 'stripe_session_id']
    readonly_fields = ['id', 'subtotal', 'shipping_fee', 'tax', 'total', 'created_at', 'updated_at']
    autocomplete_fields = ['user', 'seller']
    inlines = [OrderItemInline]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    fieldsets = (
        (_('Order Information'), {'fields': ('user', 'seller', 'status', 'payment_method')}),
        (_('Financial Details'), {'fields': ('subtotal', 'shipping_fee', 'tax', 'total')}),
        (_('Shipping Information'), {'fields': ('shipping_address', 'contact_phone', 'notes', 'stripe_session_id')}),
        (_('Metadata'), {'fields': ('id', 'created_at', 'updated_at')}),
    )

    def get_user_info(self, obj):
        return f"{obj.user.full_name} ({obj.user.email})"
    get_user_info.short_description = 'Customer'

    def get_seller_info(self, obj):
        if obj.seller:
            return obj.seller.store_name
        return "No Seller"
    get_seller_info.short_description = 'Seller'

    def get_total(self, obj):
        return f"Rs. {float(obj.total):,.2f}"
    get_total.short_description = 'Total'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'seller')


@admin.register(Cart)
class CartAdmin(ModelAdmin):
    list_display = ['get_user_info', 'total_items', 'subtotal', 'created_at']
    search_fields = ['user__email', 'user__full_name']
    readonly_fields = ['id', 'created_at', 'updated_at']

    def get_user_info(self, obj):
        return f"{obj.user.full_name} ({obj.user.email})"
    get_user_info.short_description = 'User'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')


@admin.register(CartItem)
class CartItemAdmin(ModelAdmin):
    list_display = ['cart', 'product', 'quantity', 'line_total', 'created_at']
    list_filter = ['created_at']
    search_fields = ['product__name', 'cart__user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('cart__user', 'product')


@admin.register(OrderItem)
class OrderItemAdmin(ModelAdmin):
    list_display = ['order', 'product_name', 'price', 'quantity', 'line_total', 'created_at']
    search_fields = ['product_name', 'order__id', 'order__user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('order__user')


@admin.register(Wishlist)
class WishlistAdmin(ModelAdmin):
    list_display = ['get_user_info', 'product', 'created_at']
    search_fields = ['user__email', 'user__full_name', 'product__name']
    readonly_fields = ['id', 'created_at', 'updated_at']

    def get_user_info(self, obj):
        return f"{obj.user.full_name} ({obj.user.email})"
    get_user_info.short_description = 'User'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'product')


@admin.register(ProductReview)
class ProductReviewAdmin(ModelAdmin):
    list_display = ['product', 'get_user_info', 'rating', 'comment_preview', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['product__name', 'user__email', 'user__full_name', 'comment']
    readonly_fields = ['id', 'created_at', 'updated_at']

    def get_user_info(self, obj):
        return f"{obj.user.full_name} ({obj.user.email})"
    get_user_info.short_description = 'Reviewer'

    def comment_preview(self, obj):
        return obj.comment[:50] + '...' if obj.comment and len(obj.comment) > 50 else obj.comment
    comment_preview.short_description = 'Comment'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'product')
