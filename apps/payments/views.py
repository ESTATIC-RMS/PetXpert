import stripe
import json
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.accounts.models import VeterinarianProfile
from apps.appointments.models import Appointment
from apps.marketplace.models import Order
from apps.marketplace.views import complete_marketplace_order_payment
from apps.core.permissions import IsPetOwner
from .models import Payment, PaymentStatus, PaymentMethod

stripe.api_key = settings.STRIPE_SECRET_KEY


class CreateCheckoutSessionView(APIView):
    permission_classes = [IsPetOwner]

    def post(self, request):
        try:
            data = json.loads(request.body)
            veterinarian_id = data.get('veterinarian_id')
            pet_id = data.get('pet_id')
            scheduled_at = data.get('scheduled_at')
            duration_minutes = data.get('duration_minutes', 60)
            reason = data.get('reason', '')
            appointment_id = data.get('appointment_id')

            veterinarian = get_object_or_404(VeterinarianProfile, id=veterinarian_id)
            consultation_fee = float(veterinarian.consultation_fee)

            tax_rate = 0.05
            tax_amount = consultation_fee * tax_rate
            total_amount = consultation_fee + tax_amount

            # Parse scheduled_at into a timezone-aware datetime
            scheduled_dt = parse_datetime(scheduled_at)
            if scheduled_dt and timezone.is_naive(scheduled_dt):
                scheduled_dt = timezone.make_aware(scheduled_dt)

            # --- Step 1: Use existing Appointment or create new one ---
            if appointment_id:
                # Use existing appointment from booking page
                appointment = Appointment.objects.get(id=appointment_id)
                # Update status to PENDING_PAYMENT
                if appointment.status != 'PENDING_PAYMENT':
                    appointment.status = 'PENDING_PAYMENT'
                    appointment.save()
            else:
                # Fallback: Create new appointment (for backward compatibility)
                appointment = Appointment.objects.create(
                    pet_owner=request.user,
                    veterinarian_id=veterinarian_id,
                    pet_id=pet_id,
                    scheduled_at=scheduled_dt,
                    duration_minutes=duration_minutes,
                    fee_charged=consultation_fee,
                    reason=reason,
                    status='PENDING_PAYMENT',
                )

            # Image must be an absolute URL for Stripe
            images = []
            if veterinarian.profile_image:
                images = [request.build_absolute_uri(veterinarian.profile_image.url)]

            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'pkr',
                            'product_data': {
                                'name': 'Veterinary Consultation',
                                'description': f'Consultation with Dr. {veterinarian.user.full_name}',
                                'images': images,
                            },
                            'unit_amount': int(round(consultation_fee * 100)),
                        },
                        'quantity': 1,
                    },
                    {
                        'price_data': {
                            'currency': 'pkr',
                            'product_data': {
                                'name': 'Tax',
                                'description': 'Service Tax (5%)',
                            },
                            'unit_amount': int(round(tax_amount * 100)),
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=request.build_absolute_uri('/payment/success/') + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri('/payment/cancel/'),
                customer_email=request.user.email,
                metadata={
                    'appointment_id': str(appointment.id),
                    'user_id': str(request.user.id),
                },
            )

            # --- Step 2: Create the Payment record with PENDING status ---
            Payment.objects.create(
                appointment=appointment,
                payer=request.user,
                amount=total_amount,
                currency='PKR',
                payment_method=PaymentMethod.STRIPE,
                status=PaymentStatus.PENDING,
                gateway='Stripe',
                gateway_txn_id=checkout_session.id,
            )

            return Response({
                'checkout_url': checkout_session.url,
                'session_id': checkout_session.id,
                'appointment_id': appointment.id,
                'consultation_fee': consultation_fee,
                'tax_amount': tax_amount,
                'total_amount': total_amount,
            })

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def payment_success(request):
    session_id = request.GET.get('session_id')
    payment_record = None
    appointment = None
    order = None
    error_msg = None

    if session_id:
        try:
            payment_record = Payment.objects.select_related('appointment', 'order').get(
                gateway_txn_id=session_id
            )
            appointment = payment_record.appointment
            order = payment_record.order

            if payment_record.status != PaymentStatus.COMPLETED:
                session = stripe.checkout.Session.retrieve(session_id)
                if session.payment_status == 'paid':
                    payment_record.status = PaymentStatus.COMPLETED
                    payment_record.paid_at = timezone.now()
                    payment_record.save()

                    if appointment and appointment.status != 'CONFIRMED':
                        appointment.status = 'CONFIRMED'
                        appointment.save()
                    elif order:
                        complete_marketplace_order_payment(payment_record)

        except Payment.DoesNotExist:
            error_msg = 'Payment record not found. If you completed payment, please contact support with your session ID.'
        except Exception as e:
            error_msg = str(e)

    return render(request, 'payments/success.html', {
        'session_id': session_id,
        'payment': payment_record,
        'appointment': appointment,
        'order': order,
        'error_msg': error_msg,
    })


def payment_cancel(request):
    order_id = request.GET.get('order_id')
    cancelled_order = None
    if order_id:
        try:
            order = Order.objects.get(id=order_id)
            if order.status == Order.OrderStatus.PENDING_PAYMENT:
                order.status = Order.OrderStatus.CANCELLED
                order.save(update_fields=['status'])
                cancelled_order = order
                from apps.marketplace.views import _notify_order_cancelled
                _notify_order_cancelled(order)
        except Order.DoesNotExist:
            pass
    return render(request, 'payments/cancel.html', {'order': cancelled_order})


def payment_page(request):
    veterinarian_id = request.GET.get('veterinarian_id')
    pet_id = request.GET.get('pet_id')
    scheduled_at = request.GET.get('scheduled_at')
    duration_minutes = request.GET.get('duration_minutes', 60)
    reason = request.GET.get('reason', '')
    appointment_id = request.GET.get('appointment_id')

    veterinarian = get_object_or_404(VeterinarianProfile, id=veterinarian_id)

    consultation_fee = float(veterinarian.consultation_fee)
    tax_rate = 0.05
    tax_amount = consultation_fee * tax_rate
    total_amount = consultation_fee + tax_amount

    context = {
        'veterinarian': veterinarian,
        'pet_id': pet_id,
        'scheduled_at': scheduled_at,
        'duration_minutes': duration_minutes,
        'reason': reason,
        'appointment_id': appointment_id,
        'consultation_fee': consultation_fee,
        'tax_amount': tax_amount,
        'total_amount': total_amount,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
    }

    return render(request, 'payments/payment.html', context)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        try:
            payment = Payment.objects.select_related('appointment', 'order').get(
                gateway_txn_id=session.id
            )

            if payment.status != PaymentStatus.COMPLETED:
                payment.status = PaymentStatus.COMPLETED
                payment.paid_at = timezone.now()
                payment.save()

            if payment.appointment and payment.appointment.status != 'CONFIRMED':
                payment.appointment.status = 'CONFIRMED'
                payment.appointment.save()
            elif payment.order:
                complete_marketplace_order_payment(payment)

        except Payment.DoesNotExist:
            pass
        except Exception:
            pass

    return HttpResponse(status=200)