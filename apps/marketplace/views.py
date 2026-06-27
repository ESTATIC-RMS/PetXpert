"""Marketplace API views."""
import uuid
from django.db import models as dm
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError, PermissionDenied
from .models import (ProductCategory, Product, ProductImage, Cart, CartItem, Order, OrderItem, Wishlist, ProductReview)

PAGE_SIZE = 12

def _serialize_product(p):
    return {
        'id': str(p.id), 'name': p.name, 'slug': p.slug, 'description': p.description,
        'price': float(p.price), 'compare_at_price': float(p.compare_at_price) if p.compare_at_price else None,
        'discount_percent': p.discount_percent, 'stock': p.stock, 'is_in_stock': p.is_in_stock,
        'image': p.image.url if p.image else None,
        'images': [{'id': str(i.id), 'url': i.image.url, 'sort_order': i.sort_order} for i in p.images.all()],
        'category': p.category.name if p.category else None, 'category_slug': p.category.slug if p.category else None,
        'pet_type': p.pet_type, 'seller_name': p.seller.store_name if p.seller else '',
        'seller_id': str(p.seller.id) if p.seller else '',
        'rating': float(p.rating), 'review_count': p.review_count, 'sales_count': p.sales_count,
        'is_featured': p.is_featured, 'created_at': p.created_at.isoformat(),
    }

class CategoryListView(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()
    def get(self, request):
        cats = ProductCategory.objects.filter(is_deleted=False).order_by('sort_order')
        return Response([{'id':str(c.id),'name':c.name,'slug':c.slug,'description':c.description,'icon':c.icon,'product_count':c.products.filter(is_active=True,is_deleted=False).count()} for c in cats])

class ProductListView(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()
    def get(self, request):
        qs = Product.objects.filter(is_active=True, is_deleted=False).select_related('category','seller').prefetch_related('images')
        cat = request.GET.get('category')
        if cat: qs = qs.filter(category__slug=cat)
        pt = request.GET.get('pet_type')
        if pt: qs = qs.filter(pet_type__icontains=pt)
        s = request.GET.get('search')
        if s: qs = qs.filter(name__icontains=s)
        sort = request.GET.get('sort','-created_at')
        valid = {'price','-price','name','-name','-created_at','created_at','-rating','-sales_count'}
        qs = qs.order_by(sort if sort in valid else '-created_at')
        page = int(request.GET.get('page',1))
        paginator = Paginator(qs, PAGE_SIZE)
        try:
            products = paginator.page(page)
        except EmptyPage:
            products = []
        return Response({'products':[_serialize_product(p) for p in products],'total':paginator.count,'pages':paginator.num_pages,'current_page':page})

class ProductDetailView(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()
    def get(self, request, product_id):
        try:
            p = Product.objects.select_related('category','seller').prefetch_related('images','reviews__user').get(id=product_id, is_active=True, is_deleted=False)
        except Product.DoesNotExist:
            raise NotFound(detail="Product not found")
        p.views_count += 1; p.save(update_fields=['views_count'])
        data = _serialize_product(p)
        data['reviews'] = [{'id':str(r.id),'user_name':r.user.full_name,'user_id':str(r.user.id),'rating':r.rating,'comment':r.comment,'created_at':r.created_at.isoformat()} for r in p.reviews.all()[:20]]
        if p.category:
            related = Product.objects.filter(category=p.category, is_active=True, is_deleted=False).exclude(id=p.id).select_related('seller').prefetch_related('images')[:6]
            data['related_products'] = [_serialize_product(r) for r in related]
        if request.user.is_authenticated:
            data['is_wishlisted'] = Wishlist.objects.filter(user=request.user, product=p).exists()
        return Response(data)

class CartView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        items = cart.items.select_related('product').prefetch_related('product__images')
        return Response({'cart_id':str(cart.id),'total_items':cart.total_items,'subtotal':float(cart.subtotal),'items':[{'id':str(i.id),'product_id':str(i.product.id),'product_name':i.product.name,'product_image':i.product.image.url if i.product.image else (i.product.images.first().image.url if i.product.images.exists() else None),'price':float(i.product.price),'quantity':i.quantity,'line_total':float(i.line_total),'stock':i.product.stock} for i in items]})
    def post(self, request):
        pid = request.data.get('product_id'); qty = int(request.data.get('quantity',1))
        if not pid: raise ValidationError(detail={'product_id':'Required'})
        try: product = Product.objects.get(id=pid, is_active=True, is_deleted=False)
        except Product.DoesNotExist: raise NotFound(detail="Not found")
        if qty > product.stock: raise ValidationError(detail={'quantity':f'Only {product.stock} available'})
        cart, _ = Cart.objects.get_or_create(user=request.user)
        item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity':qty})
        if not created: item.quantity = min(item.quantity+qty, product.stock); item.save(update_fields=['quantity'])
        return Response({'success':True,'cart_total_items':cart.total_items})
    def patch(self, request):
        iid = request.data.get('item_id'); qty = int(request.data.get('quantity',1))
        try: item = CartItem.objects.select_related('product').get(id=iid, cart__user=request.user)
        except CartItem.DoesNotExist: raise NotFound(detail="Not found")
        if qty < 1: item.delete(); return Response({'success':True,'removed':True})
        item.quantity = qty; item.save(update_fields=['quantity'])
        return Response({'success':True})
    def delete(self, request):
        iid = request.GET.get('item_id')
        if not iid: raise ValidationError(detail={'item_id':'Required'})
        CartItem.objects.filter(id=iid, cart__user=request.user).delete()
        return Response({'success':True})

class CheckoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def post(self, request):
        cart = Cart.objects.filter(user=request.user).first()
        if not cart or not cart.items.exists():
            return Response({'error':'Your cart is empty'}, status=400)
        items = cart.items.select_related('product').all()
        for item in items:
            if item.quantity > item.product.stock:
                return Response({'error':f"{item.product.name} only has {item.product.stock} in stock"}, status=400)
        from decimal import Decimal
        seller = items[0].product.seller if items[0].product.seller else None
        subtotal = sum(item.line_total for item in items)
        shipping = Decimal('200'); tax = (subtotal * Decimal('0.05')).quantize(Decimal('0.01')); total = subtotal + shipping + tax
        order = Order.objects.create(user=request.user, seller=seller, status='PROCESSING', subtotal=subtotal, shipping_fee=shipping, tax=tax, total=total, shipping_address=request.data.get('shipping_address',''), contact_phone=request.data.get('contact_phone',''))
        for item in items:
            OrderItem.objects.create(order=order, product=item.product, product_name=item.product.name, price=item.product.price, quantity=item.quantity)
            item.product.stock -= item.quantity; item.product.sales_count += item.quantity; item.product.save(update_fields=['stock','sales_count'])
        items.delete()
        _notify_order_placed(order)
        return Response({'success':True,'order_id':str(order.id),'total':float(total)})

class OrderListView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request):
        orders = Order.objects.filter(user=request.user).prefetch_related('items__product__images').order_by('-created_at')[:30]
        return Response([{'id':str(o.id),'status':o.status,'total':float(o.total),'item_count':o.items.count(),'buyer_name':o.user.full_name,'shipping_address':o.shipping_address,'contact_phone':o.contact_phone,'items':[{'product_name':i.product_name,'product_id':str(i.product.id) if i.product else None,'price':float(i.price),'quantity':i.quantity,'image':i.product.image.url if i.product and i.product.image else None} for i in o.items.all()],'created_at':o.created_at.isoformat()} for o in orders])

class WishlistView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request):
        items = Wishlist.objects.filter(user=request.user).select_related('product__category','product__seller').prefetch_related('product__images')
        return Response([_serialize_product(w.product) for w in items])
    def post(self, request):
        pid = request.data.get('product_id')
        if not pid: raise ValidationError(detail={'product_id':'Required'})
        try: product = Product.objects.get(id=pid, is_active=True, is_deleted=False)
        except Product.DoesNotExist: raise NotFound(detail="Not found")
        w, created = Wishlist.objects.get_or_create(user=request.user, product=product)
        if not created: w.delete(); return Response({'wishlisted':False})
        return Response({'wishlisted':True})

class ProductReviewView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def post(self, request, product_id):
        try: product = Product.objects.get(id=product_id, is_active=True, is_deleted=False)
        except Product.DoesNotExist: raise NotFound(detail="Not found")
        rating = int(request.data.get('rating',0)); comment = request.data.get('comment','')
        if rating < 1 or rating > 5: raise ValidationError(detail={'rating':'Must be 1-5'})
        review, _ = ProductReview.objects.update_or_create(product=product, user=request.user, defaults={'rating':rating,'comment':comment})
        avg = ProductReview.objects.filter(product=product).aggregate(dm.Avg('rating'))['rating__avg']
        product.rating = round(avg or 0, 2); product.review_count = ProductReview.objects.filter(product=product).count()
        product.save(update_fields=['rating','review_count'])
        return Response({'success':True,'review_id':str(review.id),'rating':review.rating,'product_rating':float(product.rating)})

    def delete(self, request, product_id):
        try: product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist: raise NotFound(detail="Not found")
        ProductReview.objects.filter(product=product, user=request.user).delete()
        avg = ProductReview.objects.filter(product=product).aggregate(dm.Avg('rating'))['rating__avg']
        product.rating = round(avg or 0, 2); product.review_count = ProductReview.objects.filter(product=product).count()
        product.save(update_fields=['rating','review_count'])
        return Response({'success':True,'product_rating':float(product.rating),'product_review_count':product.review_count})

def _get_seller(user):
    try: return user.seller_profile
    except Exception: raise PermissionDenied(detail="Seller profile required")

class SellerProductListView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request):
        seller = _get_seller(request.user)
        products = Product.objects.filter(seller=seller, is_deleted=False).select_related('category').prefetch_related('images').order_by('-created_at')
        return Response([_serialize_product(p) for p in products])
    def post(self, request):
        seller = _get_seller(request.user)
        name = request.data.get('name','').strip()
        if not name: raise ValidationError(detail={'name':'Required'})
        import uuid as _uuid
        slug = request.data.get('slug','').strip() or name.lower().replace(' ','-')[:260]
        if Product.objects.filter(slug=slug, is_deleted=False).exists():
            slug = slug[:250] + '-' + _uuid.uuid4().hex[:8]
        price = request.data.get('price','0') or '0'
        stock = request.data.get('stock','0') or '0'
        product = Product.objects.create(seller=seller, name=name, slug=slug, description=request.data.get('description',''), price=price, stock=int(stock), pet_type=request.data.get('pet_type',''))
        cid = request.data.get('category_id') or request.data.get('category')
        if cid:
            try: product.category = ProductCategory.objects.get(slug=cid); product.save(update_fields=['category'])
            except ProductCategory.DoesNotExist:
                try: product.category = ProductCategory.objects.get(id=cid); product.save(update_fields=['category'])
                except (ProductCategory.DoesNotExist, ValueError): pass
        for i, img in enumerate(request.FILES.getlist('images')[:8]):
            ProductImage.objects.create(product=product, image=img, sort_order=i)
        main = request.FILES.get('image')
        if main: product.image = main; product.save(update_fields=['image'])
        seller.total_products = Product.objects.filter(seller=seller, is_deleted=False).count(); seller.save(update_fields=['total_products'])
        return Response(_serialize_product(product), status=201)
    def patch(self, request):
        seller = _get_seller(request.user)
        pid = request.data.get('product_id')
        if not pid: raise ValidationError(detail={'product_id':'Required'})
        try: product = Product.objects.get(id=pid, seller=seller, is_deleted=False)
        except Product.DoesNotExist: raise NotFound(detail="Not found")
        for f in ['name','description','price','compare_at_price','stock','pet_type','is_active']:
            if f in request.data:
                val = request.data[f]
                if f in ('price','compare_at_price'): val = val or '0'
                if f == 'stock': val = int(val or 0)
                setattr(product, f, val)
        if 'category_id' in request.data:
            try: product.category = ProductCategory.objects.get(id=request.data['category_id'])
            except ProductCategory.DoesNotExist: pass
        product.save()
        return Response(_serialize_product(product))
    def delete(self, request):
        seller = _get_seller(request.user)
        pid = request.GET.get('product_id')
        if not pid: raise ValidationError(detail={'product_id':'Required'})
        try: product = Product.objects.get(id=pid, seller=seller, is_deleted=False)
        except Product.DoesNotExist: raise NotFound(detail="Not found")
        product.is_deleted = True; product.save(update_fields=['is_deleted'])
        seller.total_products = Product.objects.filter(seller=seller, is_deleted=False).count(); seller.save(update_fields=['total_products'])
        return Response({'success':True})

class SellerOrderListView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request):
        seller = _get_seller(request.user)
        orders = Order.objects.filter(seller=seller).prefetch_related('items').order_by('-created_at')[:50]
        return Response([{'id':str(o.id),'status':o.status,'total':float(o.total),'buyer_name':o.user.full_name,'buyer_email':o.user.email,'shipping_address':o.shipping_address,'contact_phone':o.contact_phone,'items':[{'product_name':i.product_name,'price':float(i.price),'quantity':i.quantity} for i in o.items.all()],'created_at':o.created_at.isoformat()} for o in orders])

class SellerOrderUpdateView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def patch(self, request, order_id):
        ns = request.data.get('status')
        # Allow order owner to cancel their own order
        if ns == 'CANCELLED':
            try: order = Order.objects.get(id=order_id, user=request.user)
            except Order.DoesNotExist: raise NotFound(detail="Not found")
            # Only allow cancellation if not already shipped/delivered/cancelled
            if order.status in ('SHIPPED', 'DELIVERED', 'CANCELLED'):
                raise ValidationError(detail={'status': f'Cannot cancel an order that is already {order.status}'})
            old_status = order.status; order.status = 'CANCELLED'; order.save(update_fields=['status'])
            # Restore stock to seller's inventory
            for item in order.items.all():
                if item.product:
                    item.product.stock += item.quantity
                    item.product.sales_count = max(0, item.product.sales_count - item.quantity)
                    item.product.save(update_fields=['stock', 'sales_count'])
            _notify_status_change(order, old_status, 'CANCELLED')
            return Response({'success':True,'status':order.status})
        # Seller updates
        seller = _get_seller(request.user)
        try: order = Order.objects.get(id=order_id, seller=seller)
        except Order.DoesNotExist: raise NotFound(detail="Not found")
        allowed = ['PROCESSING','SHIPPED','DELIVERED']
        if ns not in allowed: raise ValidationError(detail={'status':f'Must be one of: {", ".join(allowed)}'})
        old_status = order.status; order.status = ns; order.save(update_fields=['status'])
        _notify_status_change(order, old_status, ns)
        return Response({'success':True,'status':order.status})

class SellerInventoryStatsView(APIView):
    """Inventory stats: total, in_stock, low_stock, out_of_stock counts."""
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request):
        seller = _get_seller(request.user)
        products = Product.objects.filter(seller=seller, is_deleted=False)
        total = products.count()
        in_stock = products.filter(stock__gt=5).count()
        low_stock = products.filter(stock__gt=0, stock__lte=5).count()
        out_of_stock = products.filter(stock=0).count()
        return Response({
            'total_products': total, 'in_stock': in_stock,
            'low_stock': low_stock, 'out_of_stock': out_of_stock,
            'store_name': seller.store_name,
        })


# ── Notification helpers ──────────────────────────────────────────────

def _notify_order_placed(order):
    """Create notification for the buyer when their order is placed."""
    try:
        from apps.notifications.models import Notification, NotificationType
        items = order.items.all()
        names = ', '.join(i.product_name for i in items[:3])
        if items.count() > 3: names += f' and {items.count()-3} more'
        Notification.objects.create(
            recipient=order.user,
            title='Order Placed',
            content=f'Your order ({names}) has been placed and is being processed.',
            notification_type=NotificationType.ORDER_PLACED,
            related_id=order.id,
            related_type='order',
        )
    except Exception: pass


def _notify_status_change(order, old_status, new_status):
    """Create notification for the buyer when their order status changes."""
    try:
        from apps.notifications.models import Notification, NotificationType
        labels = {'PROCESSING':'Processing','SHIPPED':'Shipped','DELIVERED':'Delivered','CANCELLED':'Cancelled'}
        items = order.items.all()
        names = ', '.join(i.product_name for i in items[:3])
        if items.count() > 3: names += f' and {items.count()-3} more'
        Notification.objects.create(
            recipient=order.user,
            title=f'Order {labels.get(new_status, new_status)}',
            content=f'Your order ({names}) status changed to {labels.get(new_status, new_status)}.',
            notification_type=NotificationType.ORDER_STATUS_CHANGED,
            related_id=order.id,
            related_type='order',
        )
    except Exception: pass

class SellerSalesSummaryView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request):
        seller = _get_seller(request.user)
        orders = Order.objects.filter(seller=seller)
        revenue = sum(float(o.total) for o in orders.filter(status__in=['PAID','PROCESSING','SHIPPED','DELIVERED']))
        return Response({'total_revenue':round(revenue,2),'total_orders':orders.count(),'pending_orders':orders.filter(status__in=['PENDING_PAYMENT','PAID','PROCESSING']).count(),'products_count':Product.objects.filter(seller=seller,is_deleted=False).count(),'store_name':seller.store_name})
