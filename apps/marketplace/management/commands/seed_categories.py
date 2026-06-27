from django.core.management.base import BaseCommand
from apps.marketplace.models import ProductCategory

CATEGORIES = [
    {"name": "Pet Food", "icon": "utensils", "description": "Dry food, wet food, treats & supplements"},
    {"name": "Toys", "icon": "gamepad-2", "description": "Chew toys, balls, puzzles & interactive toys"},
    {"name": "Collars", "icon": "circle", "description": "Collars, tags & identification"},
    {"name": "Leashes", "icon": "link", "description": "Standard, retractable & training leashes"},
    {"name": "Beds", "icon": "bed", "description": "Beds, mats, blankets & pillows"},
    {"name": "Grooming", "icon": "scissors", "description": "Shampoos, brushes, clippers & grooming tools"},
    {"name": "Healthcare", "icon": "heart-pulse", "description": "Medicine, supplements, first aid & wellness"},
    {"name": "Clothing", "icon": "shirt", "description": "Jackets, sweaters, boots & costumes"},
    {"name": "Bowls & Feeders", "icon": "cup-soda", "description": "Food bowls, water fountains & automatic feeders"},
    {"name": "Carriers", "icon": "briefcase", "description": "Travel carriers, crates & strollers"},
    {"name": "Accessories", "icon": "gem", "description": "Bandanas, bows, sunglasses & fashion accessories"},
    {"name": "Other", "icon": "package", "description": "Everything else for your pet"},
]

class Command(BaseCommand):
    help = "Seed the 12 marketplace product categories"

    def handle(self, *args, **options):
        created = 0
        for i, cat in enumerate(CATEGORIES):
            _, is_new = ProductCategory.objects.get_or_create(
                slug=cat["name"].lower().replace(" & ", "-").replace(" ", "-"),
                defaults={"name": cat["name"], "icon": cat["icon"], "description": cat["description"], "sort_order": i},
            )
            if is_new: created += 1
            self.stdout.write(self.style.SUCCESS(f"  {'Created' if is_new else 'Exists'}: {cat['name']}"))
        self.stdout.write(self.style.SUCCESS(f"\nDone — {created} new categories created."))
