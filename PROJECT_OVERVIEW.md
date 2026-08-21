# PetXpert — Project Overview

## What is PetXpert?

PetXpert is an AI-powered pet healthcare and marketplace platform built with Django. It connects pet owners, veterinarians, and pet-product sellers in one system. Pet owners can manage pet records, receive AI-assisted health guidance, book veterinary consultations, access prescriptions, shop for pet products, and join a community. Veterinarians can manage appointments and prescriptions, while sellers can manage products and customer orders.

## Users

- **Pet Owners:** Manage pets, use AI diagnosis, book veterinarians, view prescriptions, shop, and participate in the community.
- **Veterinarians:** Maintain professional profiles, manage appointments, issue prescriptions, and receive reviews.
- **Sellers:** Manage store profiles, products, inventory, orders, and sales.
- **Administrators:** Oversee users, healthcare services, marketplace activity, payments, notifications, and community content.

## Main Functionalities

### AI-Assisted Pet Diagnosis
Pet owners can upload an image and provide symptoms for an AI-assisted health assessment. The system uses machine-learning image analysis and an AI assistant to present possible conditions, severity, risk information, and guidance. Previous diagnosis records are saved for reference. This feature currently focuses mainly on dogs and is intended as preliminary guidance, not a replacement for a veterinarian.

### Pet Profile Management
Owners can create and maintain profiles for their pets, including species, breed, date of birth, weight, allergies, microchip details, and profile pictures. These records provide a central history for each pet.

### Veterinarian Services and Appointments
Users can browse veterinarian profiles, review professional and clinic information, check available time slots, and book consultations. Owners and veterinarians can track appointments and update their status. Consultation payments can be completed securely through Stripe.

### Digital Prescriptions
Veterinarians can create prescriptions and add medication instructions after consultations. Pet owners can access prescription details through their accounts, creating a convenient digital healthcare record.

### Pet Marketplace
The marketplace allows customers to browse products by category, view product details, maintain a cart and wishlist, submit reviews, and place orders using cash on delivery or Stripe. Sellers can add products, manage stock, process orders, and monitor sales and inventory statistics.

### Community Chat
PetXpert includes a real-time group community where users can exchange messages and attachments. Django Channels and WebSockets provide live communication between pet owners, veterinarians, and sellers.

### Notifications
Users receive notifications for important events such as appointment updates, payments, reviews, and order status changes. Notifications can be viewed and marked as read from the platform header.

### Administration
The customized administration dashboard enables platform staff to manage accounts, veterinarian verification, pets, appointments, prescriptions, diagnoses, products, orders, payments, notifications, and community activity.

## Technology and Integrations

PetXpert uses **Django 5**, Django REST Framework with JWT authentication, SQLite for development, Django Channels for real-time chat, PyTorch and OpenCLIP for image analysis, Groq for AI-generated explanations, and Stripe for online payments. The platform supports role-based access so each user sees tools and navigation relevant to their responsibilities.

## Project Purpose

PetXpert brings essential pet-care services into a single digital platform. Its goal is to make early health guidance, professional veterinary support, pet records, prescriptions, trusted products, and community assistance easier to access and manage.
