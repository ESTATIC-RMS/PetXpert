from django.contrib import admin
from .models import ProductCategory, Product, ProductImage, Cart, CartItem, Order, OrderItem, Wishlist, ProductReview

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'sort_order')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'is_active', 'seller', 'sales_count')
    list_filter = ('category', 'is_active', 'is_featured')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('rating', 'review_count', 'sales_count', 'views_count')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'seller', 'status', 'total', 'created_at')
    list_filter = ('status',)
    readonly_fields = ('subtotal', 'shipping_fee', 'tax', 'total')

admin.site.register(ProductImage)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(OrderItem)
admin.site.register(Wishlist)
admin.site.register(ProductReview)
