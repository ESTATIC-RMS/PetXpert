from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from apps.appointments.models import Appointment
from apps.payments.models import Payment, PaymentStatus
from apps.accounts.models import VeterinarianReview
from .models import Notification, NotificationType

@receiver(post_save, sender=Appointment)
def appointment_notification_trigger(sender, instance, created, **kwargs):
    vet_user = instance.veterinarian.user if instance.veterinarian else None
    pet_owner = instance.pet_owner
    scheduled_str = instance.scheduled_at.astimezone(timezone.get_current_timezone()).strftime('%I:%M %p on %b %d, %Y')
    vet_name = vet_user.full_name if vet_user else "Veterinarian"
    pet_name = instance.pet.name if instance.pet else "your pet"
    owner_name = pet_owner.full_name if pet_owner else "Pet Owner"

    if created:
        # 1. Appointment Created notification to BOTH owner and vet
        # Pet Owner Notification
        Notification.objects.create(
            recipient=pet_owner,
            title="Appointment Requested",
            content=f"You have requested an appointment with Dr. {vet_name} for {pet_name} at {scheduled_str}.",
            notification_type=NotificationType.APPOINTMENT_CREATED,
            related_id=instance.id,
            related_type="appointment"
        )
        
        # Vet Notification
        if vet_user:
            Notification.objects.create(
                recipient=vet_user,
                title="New Appointment Request",
                content=f"You have a new appointment request from {owner_name} for {pet_name} at {scheduled_str}.",
                notification_type=NotificationType.APPOINTMENT_CREATED,
                related_id=instance.id,
                related_type="appointment"
            )
    else:
        # Check transitions
        if instance.status == 'CANCELLED':
            # Check if cancellation notification already exists to avoid duplicates
            if not Notification.objects.filter(related_id=instance.id, notification_type=NotificationType.APPOINTMENT_CANCELLED).exists():
                by_str = ""
                if instance.cancelled_by:
                    by_str = f" by {instance.cancelled_by.full_name}"
                
                # Notify Owner
                Notification.objects.create(
                    recipient=pet_owner,
                    title="Appointment Cancelled",
                    content=f"Your appointment with Dr. {vet_name} scheduled for {scheduled_str} has been cancelled{by_str}.",
                    notification_type=NotificationType.APPOINTMENT_CANCELLED,
                    related_id=instance.id,
                    related_type="appointment"
                )
                
                # Notify Vet
                if vet_user:
                    Notification.objects.create(
                        recipient=vet_user,
                        title="Appointment Cancelled",
                        content=f"The appointment with {owner_name} scheduled for {scheduled_str} has been cancelled{by_str}.",
                        notification_type=NotificationType.APPOINTMENT_CANCELLED,
                        related_id=instance.id,
                        related_type="appointment"
                    )
        
        elif instance.status == 'IN_PROGRESS':
            # Check if start notification already exists
            if not Notification.objects.filter(related_id=instance.id, notification_type=NotificationType.APPOINTMENT_STARTED).exists():
                # Notify Owner
                Notification.objects.create(
                    recipient=pet_owner,
                    title="Appointment Started",
                    content=f"Dr. {vet_name} has started your appointment for {pet_name}. Please join the consultation session now.",
                    notification_type=NotificationType.APPOINTMENT_STARTED,
                    related_id=instance.id,
                    related_type="appointment"
                )
                
                # Notify Vet
                if vet_user:
                    Notification.objects.create(
                        recipient=vet_user,
                        title="Appointment Started",
                        content=f"You have started your appointment with {owner_name} for {pet_name}.",
                        notification_type=NotificationType.APPOINTMENT_STARTED,
                        related_id=instance.id,
                        related_type="appointment"
                    )
        
        elif instance.status == 'COMPLETED':
            # Check if completion notification already exists
            if not Notification.objects.filter(related_id=instance.id, notification_type=NotificationType.APPOINTMENT_COMPLETED).exists():
                # Notify Owner
                Notification.objects.create(
                    recipient=pet_owner,
                    title="Appointment Completed",
                    content=f"Your appointment with Dr. {vet_name} is completed. Please rate your visit and leave a review!",
                    notification_type=NotificationType.APPOINTMENT_COMPLETED,
                    related_id=instance.id,
                    related_type="appointment"
                )
                
                # Notify Vet
                if vet_user:
                    Notification.objects.create(
                        recipient=vet_user,
                        title="Appointment Completed",
                        content=f"You have marked your appointment with {owner_name} as completed.",
                        notification_type=NotificationType.APPOINTMENT_COMPLETED,
                        related_id=instance.id,
                        related_type="appointment"
                    )


@receiver(post_save, sender=Payment)
def payment_notification_trigger(sender, instance, created, **kwargs):
    # Triggers when a payment transitions to COMPLETED status
    if instance.status == PaymentStatus.COMPLETED:
        # Use Payment record ID to prevent duplicate trigger runs
        if not Notification.objects.filter(related_id=instance.id, notification_type=NotificationType.PAYMENT_RECEIVED).exists():
            appointment = instance.appointment
            payer = instance.payer
            vet_user = appointment.veterinarian.user if appointment and appointment.veterinarian else None
            vet_name = vet_user.full_name if vet_user else "Veterinarian"
            payer_name = payer.full_name if payer else "Pet Owner"

            # Notify Owner (Payer)
            Notification.objects.create(
                recipient=payer,
                title="Payment Confirmed",
                content=f"Your payment of PKR {instance.amount} for the appointment with Dr. {vet_name} has been processed successfully.",
                notification_type=NotificationType.PAYMENT_RECEIVED,
                related_id=instance.id,
                related_type="payment"
            )

            # Notify Vet
            if vet_user:
                Notification.objects.create(
                    recipient=vet_user,
                    title="Payment Received",
                    content=f"Payment of PKR {instance.amount} has been received from {payer_name} for your scheduled consultation.",
                    notification_type=NotificationType.PAYMENT_RECEIVED,
                    related_id=instance.id,
                    related_type="payment"
                )


@receiver(post_save, sender=VeterinarianReview)
def review_notification_trigger(sender, instance, created, **kwargs):
    if created:
        # Notify Veterinarian when review is submitted
        vet_user = instance.veterinarian.user if instance.veterinarian else None
        patient_name = instance.patient.full_name if instance.patient else "Anonymous"
        
        if vet_user:
            comment_snippet = f": \"{instance.comment[:50]}...\"" if instance.comment else "."
            Notification.objects.create(
                recipient=vet_user,
                title="New Review Received",
                content=f"You received a new {instance.rating}-star review from {patient_name}{comment_snippet}",
                notification_type=NotificationType.REVIEW_RECEIVED,
                related_id=instance.id,
                related_type="review"
            )
