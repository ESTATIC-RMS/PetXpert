from rest_framework.permissions import BasePermission, SAFE_METHODS

from apps.accounts.models import UserRole


class IsPetOwner(BasePermission):
    message = 'Only pet owners can access this resource.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == UserRole.PET_OWNER
        )


class IsVeterinarian(BasePermission):
    message = 'Only veterinarians can access this resource.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == UserRole.VETERINARIAN
        )


class IsSeller(BasePermission):
    message = 'Only sellers can access this resource.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == UserRole.SELLER
        )


class IsAdminUser(BasePermission):
    message = 'Only administrators can access this resource.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (
                request.user.role == UserRole.ADMIN
                or getattr(request.user, 'is_staff', False)
            )
        )


class IsPetOwnerOrVeterinarian(BasePermission):
    message = 'Only pet owners or veterinarians can access this resource.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in (UserRole.PET_OWNER, UserRole.VETERINARIAN)
        )


class IsPetOwnerOrSeller(BasePermission):
    message = 'Only pet owners or sellers can access this resource.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in (UserRole.PET_OWNER, UserRole.SELLER)
        )


class IsReadOnlyOrPetOwner(BasePermission):
    """Allow anyone authenticated to read; writes restricted to pet owners."""

    message = 'Only pet owners can perform this action.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.role == UserRole.PET_OWNER


class IsCommunityMember(BasePermission):
    """Pet owners, veterinarians, and sellers can use community chat."""

    message = 'You do not have access to community chat.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        return user.role in (UserRole.PET_OWNER, UserRole.VETERINARIAN, UserRole.SELLER)
