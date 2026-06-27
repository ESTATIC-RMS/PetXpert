from django.db import models
from django.conf import settings
from apps.core.models import BaseModel

class ProductCategory(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True, help_text="Lucide icon name")
    image = models.ImageField(upload_to='marketplace/categories/', null=True, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0, db_index=True)
    class Meta:
        db_table = 'marketplace_category'
        verbose_name_plural = 'Product Categories'
        ordering = ['sort_order', 'name']
    def __str__(self): return self.name

class Product(BaseModel):
    seller = models.ForeignKey('accounts.SellerProfile', on_delete=models.CASCADE, related_name='products', db_index=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, related_name='products', db_index=True)
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=280, unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='marketplace/products/', null=True, blank=True)
    pet_type = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    review_count = models.PositiveIntegerField(default=0)
    sales_count = models.PositiveIntegerField(default=0)
    views_count = models.PositiveIntegerField(default=0)
    class Meta:
        db_table = 'marketplace_product'
        ordering = ['-created_at']
    def __str__(self): return self.name
    @property
    def discount_percent(self):
        if self.compare_at_price and self.compare_at_price > self.price:
            return round((1 - self.price / self.compare_at_price) * 100)
        return None
    @property
    def is_in_stock(self): return self.stock > 0

class ProductImage(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='marketplace/products/')
    sort_order = models.PositiveSmallIntegerField(default=0)
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    class Meta:
        db_table = 'marketplace_productimage'
        ordering = ['sort_order', 'created_at']

class Cart(BaseModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    class Meta: db_table = 'marketplace_cart'
    @property
    def total_items(self): return sum(i.quantity for i in self.items.all())
    @property
    def subtotal(self): return sum(i.line_total for i in self.items.all())

class CartItem(BaseModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField(default=1)
    class Meta:
        db_table = 'marketplace_cartitem'
        unique_together = [['cart', 'product']]
    @property
    def line_total(self): return self.product.price * self.quantity

class Order(BaseModel):
    class OrderStatus(models.TextChoices):
        PENDING_PAYMENT = 'PENDING_PAYMENT', 'Pending Payment'
        PAID = 'PAID', 'Paid'
        PROCESSING = 'PROCESSING', 'Processing'
        SHIPPED = 'SHIPPED', 'Shipped'
        DELIVERED = 'DELIVERED', 'Delivered'
        CANCELLED = 'CANCELLED', 'Cancelled'
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='marketplace_orders', db_index=True)
    seller = models.ForeignKey('accounts.SellerProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='received_orders', db_index=True)
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING_PAYMENT, db_index=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.TextField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    class Meta:
        db_table = 'marketplace_order'
        ordering = ['-created_at']
    def __str__(self): return f"Order #{self.id.hex[:8]}"

class OrderItem(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveSmallIntegerField(default=1)
    class Meta: db_table = 'marketplace_orderitem'
    @property
    def line_total(self): return self.price * self.quantity

class Wishlist(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    class Meta:
        db_table = 'marketplace_wishlist'
        unique_together = [['user', 'product']]
        ordering = ['-created_at']

class ProductReview(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(db_index=True)
    comment = models.TextField(blank=True, null=True)
    class Meta:
        db_table = 'marketplace_review'
        unique_together = [['product', 'user']]
        ordering = ['-created_at']
        constraints = [models.CheckConstraint(condition=models.Q(rating__gte=1) & models.Q(rating__lte=5), name='chk_product_rating')]
