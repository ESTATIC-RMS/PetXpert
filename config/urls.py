from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from apps.accounts.views import (
    SignupView, SigninView, ProfileImageUploadView, ProfileImageDeleteView,
    UserProfileView, VeterinarianProfileImageUploadView, VeterinarianProfileImageDeleteView,
    VeterinarianProfileUpdateView, VeterinarianListView,
    VeterinarianReviewListCreateView, VeterinarianReviewDetailView,
    UserReviewListView, AppointmentReviewView, veterinarian_detail_page, book_appointment_page,
    DashboardStatsView, PublicStatsView
)
from apps.appointments.views import AvailableTimeSlotsView, AppointmentListCreateView, AppointmentStatusUpdateView
from apps.payments.views import (
    CreateCheckoutSessionView, 
    payment_page, payment_success, payment_cancel, stripe_webhook
)

def index(request):
    return render(request, 'home/index.html')

def signup_page(request):
    return render(request, 'auth/signup.html')

def signin_page(request):
    return render(request, 'auth/signin.html')

def veterinarians_page(request):
    return render(request, 'veterinarians/list.html')

def vet_profile_complete_page(request):
    return render(request, 'veterinarians/profile_complete.html')

def my_pets_page(request):
    return render(request, 'pets/my_pets.html')

def dashboard_page(request):
    return render(request, 'dashboard/dashboard.html')

def appointments_page(request):
    return render(request, 'appointments/appointments.html')

def prescriptions_page(request):
    return render(request, 'prescriptions/prescriptions.html')

def chat_page(request):
    return render(request, 'chat/community.html')

def diagnosis_page(request):
    return render(request, 'diagnosis/diagnosis.html')

def marketplace_page(request):
    return render(request, 'marketplace/marketplace.html')

def marketplace_product_page(request, product_id):
    return render(request, 'marketplace/product_detail.html', {'product_id': product_id})

def marketplace_cart_page(request):
    return render(request, 'marketplace/cart.html')

def marketplace_checkout_page(request):
    return render(request, 'marketplace/checkout.html')

def marketplace_order_confirmation_page(request):
    return render(request, 'marketplace/order_confirmation.html')

def marketplace_orders_page(request):
    return render(request, 'marketplace/orders.html')

def marketplace_wishlist_page(request):
    return render(request, 'marketplace/wishlist.html')

def marketplace_buyer_dashboard_page(request):
    return render(request, 'marketplace/orders.html')

def seller_profile_complete_page(request):
    return render(request, 'marketplace/seller_dashboard.html')

def seller_dashboard_page(request):
    return render(request, 'marketplace/seller_dashboard.html')

def seller_products_page(request):
    return render(request, 'marketplace/inventory.html')

def seller_add_product_page(request):
    return render(request, 'marketplace/inventory_add.html')

def seller_orders_page(request):
    return render(request, 'marketplace/orders.html')

def seller_inventory_page(request):
    return render(request, 'marketplace/inventory.html')

def seller_reviews_page(request):
    return render(request, 'marketplace/seller_dashboard.html')

def marketplace_admin_page(request):
    return render(request, 'marketplace/admin/dashboard.html')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('signup/', signup_page, name='signup_page'),
    path('signin/', signin_page, name='signin_page'),
    path('community/', chat_page, name='chat_page'),
    path('ai-diagnosis/', diagnosis_page, name='diagnosis_page'),
    path('marketplace/', marketplace_page, name='marketplace_page'),
    path('marketplace/product/<uuid:product_id>/', marketplace_product_page, name='marketplace_product_page'),
    path('marketplace/cart/', marketplace_cart_page, name='marketplace_cart_page'),
    path('marketplace/checkout/', marketplace_checkout_page, name='marketplace_checkout_page'),
    path('marketplace/order-confirmation/', marketplace_order_confirmation_page, name='marketplace_order_confirmation_page'),
    path('marketplace/orders/', marketplace_orders_page, name='marketplace_orders_page'),
    path('marketplace/orders/manage/', marketplace_orders_page, name='marketplace_orders_manage'),
    path('marketplace/wishlist/', marketplace_wishlist_page, name='marketplace_wishlist'),
    path('marketplace/inventory/', seller_inventory_page, name='marketplace_inventory'),
    path('marketplace/inventory/add/', seller_add_product_page, name='marketplace_inventory_add'),
    path('marketplace/dashboard/', marketplace_buyer_dashboard_page, name='marketplace_buyer_dashboard_page'),
    path('marketplace/seller/complete-profile/', seller_profile_complete_page, name='seller_profile_complete'),
    path('marketplace/seller/dashboard/', seller_dashboard_page, name='seller_dashboard_page'),
    path('marketplace/seller/products/', seller_products_page, name='seller_products_page'),
    path('marketplace/seller/products/add/', seller_add_product_page, name='seller_add_product_page'),
    path('marketplace/seller/orders/', seller_orders_page, name='seller_orders_page'),
    path('marketplace/seller/inventory/', seller_inventory_page, name='seller_inventory_page'),
    path('marketplace/seller/reviews/', seller_reviews_page, name='seller_reviews_page'),
    path('marketplace/admin/', marketplace_admin_page, name='marketplace_admin_page'),
    path('dashboard/', dashboard_page, name='dashboard_page'),
    path('appointments/', appointments_page, name='appointments_page'),
    path('prescriptions/', prescriptions_page, name='prescriptions_page'),
    path('veterinarians/', veterinarians_page, name='veterinarians_page'),
    path('veterinarians/<uuid:veterinarian_id>/', veterinarian_detail_page, name='veterinarian_detail'),
    path('veterinarians/<uuid:veterinarian_id>/book/', book_appointment_page, name='book_appointment'),
    path('my-pets/', my_pets_page, name='my_pets_page'),
    path('api/signup/', SignupView.as_view(), name='api_signup'),
    path('api/signin/', SigninView.as_view(), name='api_signin'),
    path('api/public/stats/', PublicStatsView.as_view(), name='api_public_stats'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/profile/', UserProfileView.as_view(), name='api_profile'),
    path('api/profile/avatar/upload/', ProfileImageUploadView.as_view(), name='api_avatar_upload'),
    path('api/profile/avatar/delete/', ProfileImageDeleteView.as_view(), name='api_avatar_delete'),
    path('api/profile/vet/avatar/upload/', VeterinarianProfileImageUploadView.as_view(), name='api_vet_avatar_upload'),
    path('api/profile/vet/avatar/delete/', VeterinarianProfileImageDeleteView.as_view(), name='api_vet_avatar_delete'),
    path('api/profile/vet/update/', VeterinarianProfileUpdateView.as_view(), name='api_vet_profile_update'),
    path('api/veterinarians/', VeterinarianListView.as_view(), name='api_veterinarians'),
    path('api/pets/', include('apps.pets.urls')),
    path('veterinarian/complete-profile/', vet_profile_complete_page, name='vet_profile_complete'),
    # Review endpoints
    path('api/veterinarians/<uuid:veterinarian_id>/reviews/', VeterinarianReviewListCreateView.as_view(), name='api_vet_review_list_create'),
    path('api/reviews/<uuid:review_id>/', VeterinarianReviewDetailView.as_view(), name='api_vet_review_detail'),
    path('api/reviews/my/', UserReviewListView.as_view(), name='api_my_reviews'),
    path('api/appointments/<uuid:appointment_id>/review/', AppointmentReviewView.as_view(), name='api_appointment_review'),
    path('api/appointments/available-slots/', AvailableTimeSlotsView.as_view(), name='api_available_slots'),
    path('api/appointments/', AppointmentListCreateView.as_view(), name='api_appointments'),
    path('api/chat/', include('apps.chat.urls')),
    path('api/diagnosis/', include('apps.diagnosis.urls')),
    path('api/appointments/<uuid:appointment_id>/status/', AppointmentStatusUpdateView.as_view(), name='api_appointment_status'),
    path('api/dashboard/stats/', DashboardStatsView.as_view(), name='api_dashboard_stats'),
    path('api/prescriptions/', include('apps.prescriptions.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/marketplace/', include('apps.marketplace.urls')),
    # Payment endpoints
    path('api/payments/create-checkout-session/', CreateCheckoutSessionView.as_view(), name='api_create_checkout_session'),
    path('payment/', payment_page, name='payment_page'),
    path('payment/success/', payment_success, name='payment_success'),
    path('payment/cancel/', payment_cancel, name='payment_cancel'),
    path('api/webhooks/stripe/', stripe_webhook, name='stripe_webhook'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
