"""
PetXpert Admin Dashboard callback for django-unfold.

Injects platform statistics and recent activity into templates/admin/index.html
via the UNFOLD["DASHBOARD_CALLBACK"] setting.
"""
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


def dashboard_callback(request, context):
    """Prepare dashboard metrics for the custom admin index template."""
    from apps.pets.models import Pet
    from apps.accounts.models import VeterinarianProfile, SellerProfile, UserRole
    from apps.appointments.models import Appointment
    from apps.marketplace.models import Product, Order
    from apps.diagnosis.models import DiagnosisRecord

    recent_users = (
        User.objects.filter(is_deleted=False)
        .order_by('-created_at')[:8]
    )
    recent_orders = (
        Order.objects.filter(is_deleted=False)
        .select_related('user', 'seller')
        .order_by('-created_at')[:8]
    )
    recent_appointments = (
        Appointment.objects.filter(is_deleted=False)
        .select_related('pet_owner', 'veterinarian', 'pet')
        .order_by('-created_at')[:8]
    )

    week_ago = timezone.now() - timedelta(days=7)
    new_users_week = User.objects.filter(created_at__gte=week_ago, is_deleted=False).count()

    context.update({
        'stats': {
            'total_users': User.objects.filter(is_deleted=False).count(),
            'total_pets': Pet.objects.filter(is_deleted=False).count(),
            'total_sellers': SellerProfile.objects.filter(is_deleted=False).count(),
            'total_veterinarians': VeterinarianProfile.objects.filter(is_deleted=False).count(),
            'total_diagnoses': DiagnosisRecord.objects.filter(is_deleted=False).count(),
            'total_products': Product.objects.filter(is_deleted=False).count(),
            'total_orders': Order.objects.filter(is_deleted=False).count(),
            'new_users_week': new_users_week,
            'pet_owners': User.objects.filter(role=UserRole.PET_OWNER, is_deleted=False).count(),
        },
        'recent_users': recent_users,
        'recent_orders': recent_orders,
        'recent_appointments': recent_appointments,
    })
    return context


def environment_callback(request):
    """Display environment badge in admin header."""
    from django.conf import settings
    if settings.DEBUG:
        return ['Development', 'warning']
    return ['Production', 'success']
