# PetXpert Django Admin Customization

This document describes every customization made to the Django Admin interface.
All changes preserve native `django.contrib.admin` functionality — CRUD, permissions,
filters, search, pagination, inlines, and actions remain unchanged.

## Package Choice: django-unfold

**Package:** [django-unfold](https://github.com/unfoldadmin/django-unfold) v0.99+  
**Why:** Actively maintained, compatible with Django 5.2, and designed as a skin
over `django.contrib.admin` (not a replacement). It provides:

- Modern SaaS-style sidebar with Material icons
- Built-in light/dark mode toggle
- Styled forms, tables, filters, and pagination
- Dashboard callback API for custom homepage widgets
- Template override support without forking Django internals

Alternatives considered: **django-jazzmin** (older aesthetic), **django-grappelli**
(legacy). Unfold best matches the Stripe/Linear/Vercel design target.

## Files Changed

### Configuration

| File | Change |
|------|--------|
| `requirements/base.txt` | Added `django-unfold>=0.99.0` |
| `config/settings/development.py` | Added unfold apps before `django.contrib.admin`; full `UNFOLD` dict with PetXpert branding, sidebar navigation, colors, login image, custom CSS/JS |
| `config/urls.py` | Set `admin.site.site_header`, `site_title`, `index_title` |

### Dashboard Logic

| File | Purpose |
|------|---------|
| `apps/core/admin_dashboard.py` | `dashboard_callback()` injects platform stats and recent activity; `environment_callback()` shows Development/Production badge |

### Templates (override Django Admin)

| File | Purpose |
|------|---------|
| `templates/admin/index.html` | Custom dashboard: stat cards, quick actions, recent users/orders/appointments |
| `templates/admin/logged_out.html` | Branded logout confirmation page |
| `templates/admin/403.html` | Permission denied error page |
| `templates/admin/404.html` | Not found error page |
| `templates/admin/500.html` | Server error page |

### Static Assets

| File | Purpose |
|------|---------|
| `static/admin/css/petxpert-admin.css` | PetXpert brand styles: stat cards, panels, badges, table polish, toasts, error pages |
| `static/admin/js/petxpert-admin.js` | Minimal JS: row hover class, auto-dismiss toast messages |

### Admin Classes (unfold.admin.ModelAdmin)

All `ModelAdmin` classes were updated from `django.contrib.admin.ModelAdmin`
to `unfold.admin.ModelAdmin` for proper form styling. `TabularInline` updated
to `unfold.admin.TabularInline` where used.

| App | Models registered |
|-----|-------------------|
| `accounts` | User, VeterinarianProfile, **SellerProfile** (new), VeterinarianReview |
| `pets` | Pet |
| `appointments` | Appointment |
| `prescriptions` | Prescription, PrescriptionItem |
| `payments` | Payment |
| `chat` | ChatGroup, Message, Attachment |
| `marketplace` | ProductCategory, Product, Order, Cart, CartItem, OrderItem, Wishlist, ProductReview |
| `diagnosis` | **DiagnosisRecord** (new) |
| `notifications` | **Notification** (new) |

## UNFOLD Settings Summary

- **SITE_TITLE / SITE_HEADER:** PetXpert branding
- **SITE_LOGO / SITE_ICON / SITE_FAVICONS:** `static/images/petxpert_logo.png`
- **COLORS.primary:** `#003FB1` palette (PetXpert brand blue)
- **LOGIN.image:** `static/images/hero.png` background on login page
- **SIDEBAR:** Grouped navigation (Overview, Users, Healthcare, Marketplace, System) + `show_all_applications: True` so no model is hidden
- **DASHBOARD_CALLBACK:** `apps.core.admin_dashboard.dashboard_callback`
- **STYLES / SCRIPTS:** Custom PetXpert CSS and JS
- **Dark mode:** Enabled via unfold's built-in theme switcher (not forced)

## Dashboard Metrics

The admin homepage displays:

- Total Users (+ new this week)
- Total Pets
- Total Sellers
- Total Veterinarians
- Total AI Diagnoses
- Total Marketplace Products
- Total Orders
- Pet Owners count
- Recent Users, Orders, and Appointments tables

## What Was NOT Changed

- No custom admin panel or replacement routing
- No modification to model logic, views, or API endpoints
- No changes to authentication or permission backends
- Django Admin URL remains `/admin/`
- All existing admin registrations preserved and enhanced

## Upgrading

When upgrading Django or django-unfold:

1. Check [unfold changelog](https://github.com/unfoldadmin/django-unfold/releases) for breaking changes
2. Run `pip install -U django-unfold`
3. Test `/admin/` dashboard, a changelist, and a change form
4. Verify custom `templates/admin/index.html` still extends `admin/base.html`

## Access

Visit `/admin/` and sign in with a superuser account.
Create one with: `python manage.py createsuperuser`
