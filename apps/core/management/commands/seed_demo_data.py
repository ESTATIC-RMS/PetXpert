"""
Load a realistic demo dataset for PetXpert.

Usage:
    python manage.py seed_demo_data
    python manage.py seed_demo_data --reset
"""
from datetime import date, timedelta
from decimal import Decimal

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.accounts.models import (
    SellerProfile,
    User,
    UserRole,
    VeterinarianProfile,
    VeterinarianReview,
    VeterinarianStatus,
)
from apps.appointments.models import Appointment, AppointmentStatus
from apps.chat.models import ChatGroup, Message, MessageType
from apps.diagnosis.models import (
    DiagnosisInputType,
    DiagnosisRecord,
    DiagnosisSeverity,
    DiagnosisStatus,
)
from apps.marketplace.models import (
    Cart,
    CartItem,
    Order,
    OrderItem,
    Product,
    ProductCategory,
    ProductReview,
    Wishlist,
)
from apps.notifications.models import Notification, NotificationType
from apps.payments.models import Payment, PaymentMethod, PaymentStatus
from apps.pets.models import Pet, PetGender, PetSpecies
from apps.prescriptions.models import Prescription, PrescriptionItem

DEMO_PASSWORD = 'DemoPass123!'


class Command(BaseCommand):
    help = 'Insert demo users, pets, appointments, products, and related records.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete previously seeded demo records before inserting again.',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self._reset_demo_data()

        with transaction.atomic():
            users = self._seed_users()
            vets = self._seed_veterinarians(users)
            sellers = self._seed_sellers(users)
            pets = self._seed_pets(users)
            appointments = self._seed_appointments(users, vets, pets)
            self._seed_reviews(users, vets, appointments)
            self._seed_prescriptions(vets, pets, appointments)
            self._seed_diagnoses(users, pets)
            categories = self._seed_categories()
            products = self._seed_products(sellers, categories)
            orders = self._seed_orders(users, sellers, products)
            self._seed_payments(users, appointments, orders)
            self._seed_cart_and_wishlist(users, products)
            self._seed_chat(users)
            self._seed_notifications(users, appointments, orders)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Demo data is ready. Sign in with:'))
        self.stdout.write('  Admin          admin@petxpert.local          DemoPass123!')
        self.stdout.write('  Pet owner      owner1@petxpert.local         DemoPass123!')
        self.stdout.write('  Pet owner      owner2@petxpert.local         DemoPass123!')
        self.stdout.write('  Veterinarian   vet1@petxpert.local           DemoPass123!')
        self.stdout.write('  Veterinarian   vet2@petxpert.local           DemoPass123!')
        self.stdout.write('  Seller         seller1@petxpert.local        DemoPass123!')
        self.stdout.write('  Seller         seller2@petxpert.local        DemoPass123!')

    def _get_or_create_user(self, email, full_name, role, **extra):
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'full_name': full_name,
                'role': role,
                'is_email_verified': True,
                'is_active': True,
                **extra,
            },
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save(update_fields=['password'])
            self.stdout.write(f'  Created user: {email}')
        else:
            changed = False
            if user.full_name != full_name:
                user.full_name = full_name
                changed = True
            if user.role != role:
                user.role = role
                changed = True
            for key, value in extra.items():
                if getattr(user, key) != value:
                    setattr(user, key, value)
                    changed = True
            if changed:
                user.save()
            self.stdout.write(f'  Exists user: {email}')
        return user

    def _seed_users(self):
        self.stdout.write(self.style.NOTICE('Seeding users...'))
        return {
            'admin': self._get_or_create_user(
                'admin@petxpert.local',
                'PetXpert Admin',
                UserRole.ADMIN,
                is_staff=True,
                is_superuser=True,
            ),
            'owner1': self._get_or_create_user(
                'owner1@petxpert.local',
                'Ayesha Khan',
                UserRole.PET_OWNER,
            ),
            'owner2': self._get_or_create_user(
                'owner2@petxpert.local',
                'Hassan Ali',
                UserRole.PET_OWNER,
            ),
            'vet1': self._get_or_create_user(
                'vet1@petxpert.local',
                'Dr. Sara Ahmed',
                UserRole.VETERINARIAN,
            ),
            'vet2': self._get_or_create_user(
                'vet2@petxpert.local',
                'Dr. Usman Malik',
                UserRole.VETERINARIAN,
            ),
            'seller1': self._get_or_create_user(
                'seller1@petxpert.local',
                'Nadia Hussain',
                UserRole.SELLER,
            ),
            'seller2': self._get_or_create_user(
                'seller2@petxpert.local',
                'Omar Sheikh',
                UserRole.SELLER,
            ),
        }

    def _seed_veterinarians(self, users):
        self.stdout.write(self.style.NOTICE('Seeding veterinarian profiles...'))
        specs = [
            {
                'user': users['vet1'],
                'license_number': 'PK-VET-1001',
                'qualification': 'DVM, University of Veterinary & Animal Sciences',
                'specialization': 'Small Animal Medicine',
                'clinic_name': 'Paws & Care Clinic',
                'clinic_address': '12-B Gulberg III, Lahore',
                'phone_number': '+92-300-1112233',
                'consultation_fee': Decimal('2500.00'),
                'location': 'Lahore',
                'bio': 'Small-animal veterinarian focused on preventive care, dermatology, and chronic disease management for dogs and cats.',
                'years_experience': 8,
                'account_number': 'PK00DEMO0000001001',
                'status': VeterinarianStatus.VERIFIED,
                'avg_rating': Decimal('4.80'),
                'rating_count': 1,
                'total_consultations': 126,
            },
            {
                'user': users['vet2'],
                'license_number': 'PK-VET-1002',
                'qualification': 'DVM, University of Agriculture Faisalabad',
                'specialization': 'Surgery & Orthopedics',
                'clinic_name': 'City Pet Hospital',
                'clinic_address': '44 Clifton Block 5, Karachi',
                'phone_number': '+92-321-4455667',
                'consultation_fee': Decimal('3000.00'),
                'location': 'Karachi',
                'bio': 'Surgical specialist with experience in orthopedic repair, soft-tissue procedures, and emergency trauma care.',
                'years_experience': 11,
                'account_number': 'PK00DEMO0000001002',
                'status': VeterinarianStatus.VERIFIED,
                'avg_rating': Decimal('4.60'),
                'rating_count': 1,
                'total_consultations': 203,
            },
        ]
        vets = {}
        for index, data in enumerate(specs, start=1):
            user = data.pop('user')
            vet, created = VeterinarianProfile.objects.get_or_create(user=user, defaults=data)
            if not created:
                for key, value in data.items():
                    setattr(vet, key, value)
                vet.save()
            vets[f'vet{index}'] = vet
            self.stdout.write(f'  {"Created" if created else "Updated"} vet: {user.full_name}')
        return vets

    def _seed_sellers(self, users):
        self.stdout.write(self.style.NOTICE('Seeding seller profiles...'))
        specs = [
            {
                'user': users['seller1'],
                'store_name': 'Happy Paws Mart',
                'store_description': 'Premium food, toys, and daily essentials for dogs and cats.',
                'phone_number': '+92-333-7788990',
                'address': 'Shop 8, MM Alam Road, Lahore',
                'is_verified': True,
            },
            {
                'user': users['seller2'],
                'store_name': 'Urban Pet Supply',
                'store_description': 'Grooming kits, carriers, and healthcare products for urban pet parents.',
                'phone_number': '+92-345-1122334',
                'address': '23 Zamzama Commercial, Karachi',
                'is_verified': True,
            },
        ]
        sellers = {}
        for index, data in enumerate(specs, start=1):
            user = data.pop('user')
            seller, created = SellerProfile.objects.get_or_create(user=user, defaults=data)
            if not created:
                for key, value in data.items():
                    setattr(seller, key, value)
                seller.save()
            sellers[f'seller{index}'] = seller
            self.stdout.write(f'  {"Created" if created else "Updated"} seller: {seller.store_name}')
        return sellers

    def _seed_pets(self, users):
        self.stdout.write(self.style.NOTICE('Seeding pets...'))
        specs = [
            {
                'key': 'bruno',
                'owner': users['owner1'],
                'name': 'Bruno',
                'species': PetSpecies.DOG,
                'breed': 'Golden Retriever',
                'date_of_birth': date(2021, 3, 14),
                'gender': PetGender.MALE,
                'weight_kg': Decimal('28.50'),
                'is_neutered': True,
                'microchip_number': 'DEMO-CHIP-1001',
                'allergies': 'Chicken protein',
                'blood_type': 'DEA 1.1+',
            },
            {
                'key': 'milo',
                'owner': users['owner1'],
                'name': 'Milo',
                'species': PetSpecies.CAT,
                'breed': 'Persian',
                'date_of_birth': date(2022, 7, 2),
                'gender': PetGender.MALE,
                'weight_kg': Decimal('4.20'),
                'is_neutered': True,
                'microchip_number': 'DEMO-CHIP-1002',
                'allergies': None,
                'blood_type': 'A',
            },
            {
                'key': 'luna',
                'owner': users['owner2'],
                'name': 'Luna',
                'species': PetSpecies.DOG,
                'breed': 'Beagle',
                'date_of_birth': date(2020, 11, 9),
                'gender': PetGender.FEMALE,
                'weight_kg': Decimal('12.80'),
                'is_neutered': False,
                'microchip_number': 'DEMO-CHIP-2001',
                'allergies': 'Pollen',
                'blood_type': 'DEA 1.1-',
            },
        ]
        pets = {}
        for data in specs:
            key = data.pop('key')
            lookup = {'owner': data['owner'], 'name': data['name']}
            pet, created = Pet.objects.get_or_create(**lookup, defaults=data)
            if not created:
                for field, value in data.items():
                    setattr(pet, field, value)
                pet.save()
            pets[key] = pet
            self.stdout.write(f'  {"Created" if created else "Updated"} pet: {pet.name}')
        return pets

    def _seed_appointments(self, users, vets, pets):
        self.stdout.write(self.style.NOTICE('Seeding appointments...'))
        now = timezone.now()
        specs = [
            {
                'key': 'completed',
                'pet_owner': users['owner1'],
                'veterinarian': vets['vet1'],
                'pet': pets['bruno'],
                'scheduled_at': now - timedelta(days=12, hours=2),
                'duration_minutes': 60,
                'status': AppointmentStatus.COMPLETED,
                'fee_charged': vets['vet1'].consultation_fee,
                'reason': 'Itchy skin and hair loss on the back.',
            },
            {
                'key': 'confirmed',
                'pet_owner': users['owner2'],
                'veterinarian': vets['vet2'],
                'pet': pets['luna'],
                'scheduled_at': now + timedelta(days=3, hours=4),
                'duration_minutes': 60,
                'status': AppointmentStatus.CONFIRMED,
                'fee_charged': vets['vet2'].consultation_fee,
                'reason': 'Limping after a park run.',
            },
            {
                'key': 'pending',
                'pet_owner': users['owner1'],
                'veterinarian': vets['vet2'],
                'pet': pets['milo'],
                'scheduled_at': now + timedelta(days=8),
                'duration_minutes': 60,
                'status': AppointmentStatus.PENDING,
                'fee_charged': vets['vet2'].consultation_fee,
                'reason': 'Annual wellness exam and vaccination review.',
            },
        ]
        appointments = {}
        for data in specs:
            key = data.pop('key')
            appointment, created = Appointment.objects.get_or_create(
                pet_owner=data['pet_owner'],
                veterinarian=data['veterinarian'],
                pet=data['pet'],
                reason=data['reason'],
                defaults=data,
            )
            if not created:
                for field, value in data.items():
                    setattr(appointment, field, value)
                appointment.save()
            appointments[key] = appointment
            self.stdout.write(f'  {"Created" if created else "Updated"} appointment: {appointment.pet.name} ({appointment.status})')
        return appointments

    def _seed_reviews(self, users, vets, appointments):
        self.stdout.write(self.style.NOTICE('Seeding veterinarian reviews...'))
        review, created = VeterinarianReview.objects.get_or_create(
            patient=users['owner1'],
            appointment=appointments['completed'],
            defaults={
                'veterinarian': vets['vet1'],
                'rating': 5,
                'comment': 'Dr. Sara was thorough and Bruno’s skin improved within a week.',
            },
        )
        self.stdout.write(f'  {"Created" if created else "Exists"} vet review')
        return review

    def _seed_prescriptions(self, vets, pets, appointments):
        self.stdout.write(self.style.NOTICE('Seeding prescriptions...'))
        prescription, created = Prescription.objects.get_or_create(
            appointment=appointments['completed'],
            issuing_vet=vets['vet1'],
            pet=pets['bruno'],
            defaults={
                'diagnosis_text': 'Allergic dermatitis, likely food-related.',
                'instructions': 'Switch to a limited-ingredient diet and apply topical ointment twice daily.',
                'valid_until': date.today() + timedelta(days=30),
                'is_finalized': True,
            },
        )
        if created:
            PrescriptionItem.objects.create(
                prescription=prescription,
                medicine_name='Apoquel 16mg',
                dosage='1 tablet once daily',
                quantity=14,
                duration_days=14,
                notes='Give with food.',
            )
            PrescriptionItem.objects.create(
                prescription=prescription,
                medicine_name='Chlorhexidine spray',
                dosage='Apply to affected area twice daily',
                quantity=1,
                duration_days=10,
                notes='Avoid licking for 10 minutes after application.',
            )
        self.stdout.write(f'  {"Created" if created else "Exists"} prescription for Bruno')

    def _seed_diagnoses(self, users, pets):
        self.stdout.write(self.style.NOTICE('Seeding diagnosis records...'))
        record, created = DiagnosisRecord.objects.get_or_create(
            pet=pets['bruno'],
            requested_by=users['owner1'],
            celery_task_id='demo-diagnosis-bruno-001',
            defaults={
                'input_type': DiagnosisInputType.BOTH,
                'symptom_text': 'Red irritated skin and frequent scratching after meals.',
                'predicted_diseases': [
                    {'name': 'Fungal infection', 'confidence': 0.81},
                    {'name': 'Allergic dermatitis', 'confidence': 0.64},
                ],
                'severity': DiagnosisSeverity.MODERATE,
                'risk_score': Decimal('0.640'),
                'status': DiagnosisStatus.COMPLETED,
                'model_version': '1.0.0',
                'inference_time_ms': 1840,
                'llm_explanation': 'The image and symptoms are consistent with a moderate skin condition. A veterinarian visit is recommended for confirmation and treatment.',
            },
        )
        self.stdout.write(f'  {"Created" if created else "Exists"} diagnosis for Bruno')
        return record

    def _seed_categories(self):
        self.stdout.write(self.style.NOTICE('Seeding marketplace categories...'))
        call_command('seed_categories')
        return {category.slug: category for category in ProductCategory.objects.all()}

    def _seed_products(self, sellers, categories):
        self.stdout.write(self.style.NOTICE('Seeding products...'))
        specs = [
            {
                'seller': sellers['seller1'],
                'category': categories.get('pet-food'),
                'name': 'Grain-Free Adult Dog Food 5kg',
                'description': 'High-protein kibble with salmon and sweet potato. Suitable for dogs with chicken allergies.',
                'price': Decimal('4499.00'),
                'compare_at_price': Decimal('5299.00'),
                'stock': 40,
                'pet_type': 'DOG',
                'is_featured': True,
                'rating': Decimal('4.70'),
                'review_count': 1,
                'sales_count': 18,
            },
            {
                'seller': sellers['seller1'],
                'category': categories.get('toys'),
                'name': 'Interactive Puzzle Ball',
                'description': 'Slow-feed puzzle toy that keeps dogs mentally stimulated during snack time.',
                'price': Decimal('1299.00'),
                'compare_at_price': Decimal('1599.00'),
                'stock': 75,
                'pet_type': 'DOG',
                'is_featured': True,
                'rating': Decimal('4.40'),
                'review_count': 0,
                'sales_count': 31,
            },
            {
                'seller': sellers['seller2'],
                'category': categories.get('grooming'),
                'name': 'Cat Grooming Kit',
                'description': 'Soft slicker brush, nail clipper, and de-shedding comb for long-haired cats.',
                'price': Decimal('1899.00'),
                'stock': 22,
                'pet_type': 'CAT',
                'is_featured': False,
                'rating': Decimal('4.50'),
                'review_count': 0,
                'sales_count': 9,
            },
            {
                'seller': sellers['seller2'],
                'category': categories.get('healthcare'),
                'name': 'Omega-3 Skin Support Chews',
                'description': 'Daily chews that support coat shine and reduce dryness in dogs and cats.',
                'price': Decimal('2199.00'),
                'compare_at_price': Decimal('2499.00'),
                'stock': 60,
                'pet_type': 'DOG,CAT',
                'is_featured': True,
                'rating': Decimal('4.80'),
                'review_count': 1,
                'sales_count': 27,
            },
        ]
        products = {}
        for data in specs:
            slug = slugify(data['name'])
            product, created = Product.objects.get_or_create(slug=slug, defaults={**data, 'slug': slug})
            if not created:
                for field, value in data.items():
                    setattr(product, field, value)
                product.save()
            products[slug] = product
            self.stdout.write(f'  {"Created" if created else "Updated"} product: {product.name}')

        sellers['seller1'].total_products = Product.objects.filter(seller=sellers['seller1']).count()
        sellers['seller1'].save(update_fields=['total_products'])
        sellers['seller2'].total_products = Product.objects.filter(seller=sellers['seller2']).count()
        sellers['seller2'].save(update_fields=['total_products'])
        return products

    def _seed_orders(self, users, sellers, products):
        self.stdout.write(self.style.NOTICE('Seeding orders...'))
        food = products['grain-free-adult-dog-food-5kg']
        chews = products['omega-3-skin-support-chews']

        order1, created1 = Order.objects.get_or_create(
            user=users['owner1'],
            seller=sellers['seller1'],
            notes='Please leave at the gate.',
            defaults={
                'status': Order.OrderStatus.DELIVERED,
                'payment_method': Order.PaymentMethod.STRIPE,
                'subtotal': food.price,
                'shipping_fee': Decimal('150.00'),
                'tax': Decimal('0.00'),
                'total': food.price + Decimal('150.00'),
                'shipping_address': 'House 21, Street 7, DHA Phase 5, Lahore',
                'contact_phone': '+92-300-5556677',
                'stripe_session_id': 'cs_demo_order_owner1_food',
            },
        )
        if created1:
            OrderItem.objects.create(
                order=order1,
                product=food,
                product_name=food.name,
                price=food.price,
                quantity=1,
            )

        order2, created2 = Order.objects.get_or_create(
            user=users['owner2'],
            seller=sellers['seller2'],
            notes='Call before delivery.',
            defaults={
                'status': Order.OrderStatus.PROCESSING,
                'payment_method': Order.PaymentMethod.COD,
                'subtotal': chews.price * 2,
                'shipping_fee': Decimal('200.00'),
                'tax': Decimal('0.00'),
                'total': (chews.price * 2) + Decimal('200.00'),
                'shipping_address': 'Flat 4B, Ocean View, Clifton, Karachi',
                'contact_phone': '+92-321-9988776',
            },
        )
        if created2:
            OrderItem.objects.create(
                order=order2,
                product=chews,
                product_name=chews.name,
                price=chews.price,
                quantity=2,
            )

        self.stdout.write(f'  {"Created" if created1 else "Exists"} order for Ayesha')
        self.stdout.write(f'  {"Created" if created2 else "Exists"} order for Hassan')
        return {'delivered': order1, 'processing': order2}

    def _seed_payments(self, users, appointments, orders):
        self.stdout.write(self.style.NOTICE('Seeding payments...'))
        Payment.objects.get_or_create(
            gateway_txn_id='demo_appt_bruno_completed',
            defaults={
                'appointment': appointments['completed'],
                'payer': users['owner1'],
                'amount': appointments['completed'].fee_charged,
                'currency': 'PKR',
                'payment_method': PaymentMethod.STRIPE,
                'status': PaymentStatus.COMPLETED,
                'gateway': 'stripe',
                'paid_at': timezone.now() - timedelta(days=12),
            },
        )
        Payment.objects.get_or_create(
            gateway_txn_id='demo_order_ayesha_food',
            defaults={
                'order': orders['delivered'],
                'payer': users['owner1'],
                'amount': orders['delivered'].total,
                'currency': 'PKR',
                'payment_method': PaymentMethod.STRIPE,
                'status': PaymentStatus.COMPLETED,
                'gateway': 'stripe',
                'paid_at': timezone.now() - timedelta(days=6),
            },
        )
        Payment.objects.get_or_create(
            gateway_txn_id='demo_order_hassan_chews',
            defaults={
                'order': orders['processing'],
                'payer': users['owner2'],
                'amount': orders['processing'].total,
                'currency': 'PKR',
                'payment_method': PaymentMethod.CASH_ON_DELIVERY,
                'status': PaymentStatus.PENDING,
                'gateway': 'cod',
            },
        )
        self.stdout.write('  Payments synced')

    def _seed_cart_and_wishlist(self, users, products):
        self.stdout.write(self.style.NOTICE('Seeding cart and wishlist...'))
        cart, _ = Cart.objects.get_or_create(user=users['owner2'])
        CartItem.objects.get_or_create(
            cart=cart,
            product=products['interactive-puzzle-ball'],
            defaults={'quantity': 1},
        )
        Wishlist.objects.get_or_create(
            user=users['owner1'],
            product=products['omega-3-skin-support-chews'],
        )
        ProductReview.objects.get_or_create(
            product=products['grain-free-adult-dog-food-5kg'],
            user=users['owner1'],
            defaults={
                'rating': 5,
                'comment': 'Bruno loves this food and his itching has reduced.',
            },
        )
        self.stdout.write('  Cart, wishlist, and product review synced')

    def _seed_chat(self, users):
        self.stdout.write(self.style.NOTICE('Seeding community chat...'))
        group, _ = ChatGroup.objects.get_or_create(
            name='PetXpert Community',
            defaults={
                'description': 'The official PetXpert community chat for pet owners and veterinarians',
                'is_active': True,
            },
        )
        messages = [
            (users['owner1'], 'Hi everyone! Bruno has been scratching a lot after meals. Any food suggestions?'),
            (users['vet1'], 'Try a limited-ingredient diet and book a skin consult if it lasts more than a week.'),
            (users['owner2'], 'Luna loved the puzzle ball from Happy Paws Mart. Great for rainy days!'),
        ]
        for sender, content in messages:
            Message.objects.get_or_create(
                group=group,
                sender=sender,
                content=content,
                defaults={'message_type': MessageType.TEXT},
            )
        self.stdout.write('  Community messages synced')

    def _seed_notifications(self, users, appointments, orders):
        self.stdout.write(self.style.NOTICE('Seeding notifications...'))
        specs = [
            {
                'recipient': users['owner1'],
                'title': 'Appointment completed',
                'content': 'Bruno’s consultation with Dr. Sara Ahmed is complete. A prescription is now available.',
                'notification_type': NotificationType.APPOINTMENT_COMPLETED,
                'related_id': appointments['completed'].id,
                'related_type': 'appointment',
            },
            {
                'recipient': users['owner2'],
                'title': 'Appointment confirmed',
                'content': 'Luna’s appointment with Dr. Usman Malik has been confirmed.',
                'notification_type': NotificationType.APPOINTMENT_CREATED,
                'related_id': appointments['confirmed'].id,
                'related_type': 'appointment',
            },
            {
                'recipient': users['owner1'],
                'title': 'Order delivered',
                'content': 'Your Grain-Free Adult Dog Food order has been delivered.',
                'notification_type': NotificationType.ORDER_DELIVERED,
                'related_id': orders['delivered'].id,
                'related_type': 'order',
            },
            {
                'recipient': users['seller2'],
                'title': 'New marketplace order',
                'content': 'Hassan Ali placed a new order for Omega-3 Skin Support Chews.',
                'notification_type': NotificationType.SELLER_NEW_ORDER,
                'related_id': orders['processing'].id,
                'related_type': 'order',
            },
        ]
        for data in specs:
            Notification.objects.get_or_create(
                recipient=data['recipient'],
                title=data['title'],
                defaults=data,
            )
        self.stdout.write('  Notifications synced')

    def _reset_demo_data(self):
        self.stdout.write(self.style.WARNING('Removing previous demo records...'))
        demo_emails = [
            'admin@petxpert.local',
            'owner1@petxpert.local',
            'owner2@petxpert.local',
            'vet1@petxpert.local',
            'vet2@petxpert.local',
            'seller1@petxpert.local',
            'seller2@petxpert.local',
        ]
        users = User.objects.filter(email__in=demo_emails)
        Payment.objects.filter(payer__in=users).delete()
        Notification.objects.filter(recipient__in=users).delete()
        Message.objects.filter(sender__in=users).delete()
        Wishlist.objects.filter(user__in=users).delete()
        Cart.objects.filter(user__in=users).delete()
        ProductReview.objects.filter(user__in=users).delete()
        Order.objects.filter(user__in=users).delete()
        Product.objects.filter(seller__user__in=users).delete()
        DiagnosisRecord.objects.filter(requested_by__in=users).delete()
        Prescription.objects.filter(issuing_vet__user__in=users).delete()
        VeterinarianReview.objects.filter(patient__in=users).delete()
        Appointment.objects.filter(pet_owner__in=users).delete()
        Pet.objects.filter(owner__in=users).delete()
        SellerProfile.objects.filter(user__in=users).delete()
        VeterinarianProfile.objects.filter(user__in=users).delete()
        users.delete()
        self.stdout.write(self.style.WARNING('Previous demo records removed.'))
