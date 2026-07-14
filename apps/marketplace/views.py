"""Marketplace API views."""
import uuid
import stripe
from decimal import Decimal
from django.db import models as dm
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError, PermissionDenied
from apps.payments.models import Payment, PaymentMethod, PaymentStatus
from apps.accounts.models import UserRole
from apps.core.permissions import IsPetOwner, IsSeller
from .models import (ProductCategory, Product, ProductImage, Cart, CartItem, Order, OrderItem, Wishlist, ProductReview)

stripe.api_key = settings.STRIPE_SECRET_KEY

PAGE_SIZE = 6

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
        page_size = request.GET.get('page_size')
        try:
            per_page = int(page_size) if page_size else PAGE_SIZE
            per_page = max(1, min(per_page, 48))
        except (TypeError, ValueError):
            per_page = PAGE_SIZE
        page = int(request.GET.get('page',1))
        paginator = Paginator(qs, per_page)
        try:
            products = paginator.page(page)
        except EmptyPage:
            products = []
        return Response({
            'products': [_serialize_product(p) for p in products],
            'total': paginator.count,
            'pages': paginator.num_pages,
            'current_page': page,
            'page_size': per_page,
        })

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
    permission_classes = (IsPetOwner,)
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
    permission_classes = (IsPetOwner,)

    def post(self, request):
        cart = Cart.objects.filter(user=request.user).first()
        if not cart or not cart.items.exists():
            return Response({'error': 'Your cart is empty'}, status=400)

        items = list(cart.items.select_related('product').all())
        for item in items:
            if item.quantity > item.product.stock:
                return Response(
                    {'error': f"{item.product.name} only has {item.product.stock} in stock"},
                    status=400,
                )

        payment_method = (request.data.get('payment_method') or 'COD').upper()
        delivery_type = (request.data.get('delivery_type') or 'standard').lower()
        shipping_address = request.data.get('shipping_address', '')
        contact_phone = request.data.get('contact_phone', '')
        notes = request.data.get('notes', '')

        seller = items[0].product.seller if items[0].product.seller else None
        subtotal, shipping, tax, total = _calculate_order_totals(items, delivery_type)

        if payment_method == 'STRIPE':
            return self._checkout_stripe(
                request, cart, items, seller, subtotal, shipping, tax, total,
                shipping_address, contact_phone, notes,
            )
        return self._checkout_cod(
            request, cart, items, seller, subtotal, shipping, tax, total,
            shipping_address, contact_phone, notes,
        )

    def _create_order(self, user, seller, items, subtotal, shipping, tax, total,
                      shipping_address, contact_phone, notes, payment_method, status):
        order = Order.objects.create(
            user=user,
            seller=seller,
            status=status,
            payment_method=payment_method,
            subtotal=subtotal,
            shipping_fee=shipping,
            tax=tax,
            total=total,
            shipping_address=shipping_address,
            contact_phone=contact_phone,
            notes=notes,
        )
        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                price=item.product.price,
                quantity=item.quantity,
            )
        return order

    def _checkout_cod(self, request, cart, items, seller, subtotal, shipping, tax, total,
                      shipping_address, contact_phone, notes):
        order = self._create_order(
            request.user, seller, items, subtotal, shipping, tax, total,
            shipping_address, contact_phone, notes,
            Order.PaymentMethod.COD, Order.OrderStatus.PROCESSING,
        )
        _decrement_order_stock(order)
        cart.items.all().delete()

        Payment.objects.create(
            order=order,
            payer=request.user,
            amount=total,
            currency='PKR',
            payment_method=PaymentMethod.CASH_ON_DELIVERY,
            status=PaymentStatus.PENDING,
            gateway='Cash on Delivery',
            gateway_txn_id=f'cod-{order.id}',
        )

        _notify_order_confirmed(order)
        _notify_seller_new_order(order)

        return Response({
            'success': True,
            'order_id': str(order.id),
            'payment_method': 'COD',
            'total': float(total),
        })

    def _checkout_stripe(self, request, cart, items, seller, subtotal, shipping, tax, total,
                         shipping_address, contact_phone, notes):
        order = self._create_order(
            request.user, seller, items, subtotal, shipping, tax, total,
            shipping_address, contact_phone, notes,
            Order.PaymentMethod.STRIPE, Order.OrderStatus.PENDING_PAYMENT,
        )
        cart.items.all().delete()

        line_items = []
        for item in items:
            product = item.product
            images = []
            if product.image:
                images = [request.build_absolute_uri(product.image.url)]
            line_items.append({
                'price_data': {
                    'currency': 'pkr',
                    'product_data': {
                        'name': product.name,
                        'images': images,
                    },
                    'unit_amount': int(round(float(product.price) * 100)),
                },
                'quantity': item.quantity,
            })

        if float(shipping) > 0:
            line_items.append({
                'price_data': {
                    'currency': 'pkr',
                    'product_data': {'name': 'Shipping'},
                    'unit_amount': int(round(float(shipping) * 100)),
                },
                'quantity': 1,
            })
        if float(tax) > 0:
            line_items.append({
                'price_data': {
                    'currency': 'pkr',
                    'product_data': {'name': 'Tax (5%)'},
                    'unit_amount': int(round(float(tax) * 100)),
                },
                'quantity': 1,
            })

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.build_absolute_uri('/payment/success/') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri('/payment/cancel/') + f'?order_id={order.id}',
            customer_email=request.user.email,
            metadata={
                'order_id': str(order.id),
                'payment_type': 'marketplace_order',
                'user_id': str(request.user.id),
            },
        )

        order.stripe_session_id = checkout_session.id
        order.save(update_fields=['stripe_session_id'])

        Payment.objects.create(
            order=order,
            payer=request.user,
            amount=total,
            currency='PKR',
            payment_method=PaymentMethod.STRIPE,
            status=PaymentStatus.PENDING,
            gateway='Stripe',
            gateway_txn_id=checkout_session.id,
        )

        return Response({
            'success': True,
            'order_id': str(order.id),
            'payment_method': 'STRIPE',
            'checkout_url': checkout_session.url,
            'session_id': checkout_session.id,
            'total': float(total),
        })

class OrderListView(APIView):
    permission_classes = (IsPetOwner,)
    def get(self, request):
        orders = Order.objects.filter(user=request.user).prefetch_related('items__product__images').order_by('-created_at')[:30]
        return Response([{'id':str(o.id),'status':o.status,'payment_method':o.payment_method,'total':float(o.total),'item_count':o.items.count(),'buyer_name':o.user.full_name,'shipping_address':o.shipping_address,'contact_phone':o.contact_phone,'items':[{'product_name':i.product_name,'product_id':str(i.product.id) if i.product else None,'price':float(i.price),'quantity':i.quantity,'image':i.product.image.url if i.product and i.product.image else None} for i in o.items.all()],'created_at':o.created_at.isoformat()} for o in orders])

class WishlistView(APIView):
    permission_classes = (IsPetOwner,)
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
    permission_classes = (IsPetOwner,)
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
    if user.role != UserRole.SELLER:
        raise PermissionDenied(detail='Only sellers can access this resource.')
    try:
        return user.seller_profile
    except Exception:
        raise PermissionDenied(detail='Seller profile required.')

class SellerProductListView(APIView):
    permission_classes = (IsSeller,)
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
    permission_classes = (IsSeller,)
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
            if request.user.role != UserRole.PET_OWNER:
                raise PermissionDenied(detail='Only pet owners can cancel their orders.')
            try: order = Order.objects.get(id=order_id, user=request.user)
            except Order.DoesNotExist: raise NotFound(detail="Not found")
            if order.status in ('SHIPPED', 'DELIVERED', 'CANCELLED'):
                raise ValidationError(detail={'status': f'Cannot cancel an order that is already {order.status}'})
            old_status = order.status
            order.status = 'CANCELLED'
            order.save(update_fields=['status'])
            if old_status not in ('PENDING_PAYMENT',):
                for item in order.items.all():
                    if item.product:
                        item.product.stock += item.quantity
                        item.product.sales_count = max(0, item.product.sales_count - item.quantity)
                        item.product.save(update_fields=['stock', 'sales_count'])
            _notify_order_cancelled(order)
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
    permission_classes = (IsSeller,)
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


# ── Order helpers & notifications ─────────────────────────────────────

def _calculate_order_totals(items, delivery_type='standard'):
    subtotal = sum(item.line_total for item in items)
    shipping = Decimal('500') if delivery_type == 'express' else Decimal('200')
    tax = (subtotal * Decimal('0.05')).quantize(Decimal('0.01'))
    total = subtotal + shipping + tax
    return subtotal, shipping, tax, total


def _decrement_order_stock(order):
    for item in order.items.select_related('product').all():
        if item.product:
            item.product.stock = max(0, item.product.stock - item.quantity)
            item.product.sales_count += item.quantity
            item.product.save(update_fields=['stock', 'sales_count'])


def complete_marketplace_order_payment(payment):
    """Finalize a paid marketplace order (Stripe webhook / success-page fallback)."""
    order = payment.order
    if not order or order.status not in (Order.OrderStatus.PENDING_PAYMENT, Order.OrderStatus.PAID):
        return order

    if payment.status != PaymentStatus.COMPLETED:
        payment.status = PaymentStatus.COMPLETED
        payment.paid_at = timezone.now()
        payment.save(update_fields=['status', 'paid_at'])

    if order.status == Order.OrderStatus.PENDING_PAYMENT:
        order.status = Order.OrderStatus.PROCESSING
        order.save(update_fields=['status'])
        _decrement_order_stock(order)
        _notify_order_confirmed(order)
        _notify_seller_new_order(order)

    return order


def _order_item_summary(order):
    items = order.items.all()
    names = ', '.join(i.product_name for i in items[:3])
    if items.count() > 3:
        names += f' and {items.count() - 3} more'
    return names


def _notify_order_confirmed(order):
    from apps.notifications.models import Notification, NotificationType
    names = _order_item_summary(order)
    method = 'Cash on Delivery' if order.payment_method == Order.PaymentMethod.COD else 'Online Payment'
    Notification.objects.create(
        recipient=order.user,
        title='Order Confirmed',
        content=f'Your order ({names}) has been placed successfully via {method}.',
        notification_type=NotificationType.ORDER_CONFIRMED,
        related_id=order.id,
        related_type='order',
    )


def _notify_seller_new_order(order):
    from apps.notifications.models import Notification, NotificationType
    if not order.seller or not order.seller.user:
        return
    if Notification.objects.filter(
        related_id=order.id,
        notification_type=NotificationType.SELLER_NEW_ORDER,
    ).exists():
        return
    names = _order_item_summary(order)
    Notification.objects.create(
        recipient=order.seller.user,
        title='New Order Received',
        content=f'You received a new order from {order.user.full_name}: {names}.',
        notification_type=NotificationType.SELLER_NEW_ORDER,
        related_id=order.id,
        related_type='order',
    )


def _notify_order_cancelled(order):
    from apps.notifications.models import Notification, NotificationType
    names = _order_item_summary(order)
    Notification.objects.create(
        recipient=order.user,
        title='Order Cancelled',
        content=f'Your order ({names}) has been cancelled.',
        notification_type=NotificationType.ORDER_CANCELLED,
        related_id=order.id,
        related_type='order',
    )


def _notify_status_change(order, old_status, new_status):
    from apps.notifications.models import Notification, NotificationType
    type_map = {
        'PROCESSING': NotificationType.ORDER_CONFIRMED,
        'SHIPPED': NotificationType.ORDER_SHIPPED,
        'DELIVERED': NotificationType.ORDER_DELIVERED,
        'CANCELLED': NotificationType.ORDER_CANCELLED,
    }
    notification_type = type_map.get(new_status, NotificationType.GENERAL)
    labels = {
        'PROCESSING': 'Processing',
        'SHIPPED': 'Shipped',
        'DELIVERED': 'Delivered',
        'CANCELLED': 'Cancelled',
    }
    names = _order_item_summary(order)
    Notification.objects.create(
        recipient=order.user,
        title=f"Order {labels.get(new_status, new_status)}",
        content=f'Your order ({names}) status changed to {labels.get(new_status, new_status)}.',
        notification_type=notification_type,
        related_id=order.id,
        related_type='order',
    )

class SellerSalesSummaryView(APIView):
    permission_classes = (IsSeller,)
    def get(self, request):
        seller = _get_seller(request.user)
        orders = Order.objects.filter(seller=seller)
        revenue = sum(float(o.total) for o in orders.filter(status__in=['PAID','PROCESSING','SHIPPED','DELIVERED']))
        return Response({'total_revenue':round(revenue,2),'total_orders':orders.count(),'pending_orders':orders.filter(status__in=['PENDING_PAYMENT','PAID','PROCESSING']).count(),'products_count':Product.objects.filter(seller=seller,is_deleted=False).count(),'store_name':seller.store_name})
