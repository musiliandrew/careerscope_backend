from rest_framework.permissions import BasePermission

class RequiresProTier(BasePermission):
    """
    Allows access only to users with a 'pro' or 'premium' subscription tier.
    """
    message = "You must upgrade to the Pro or Premium tier to access this feature."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Access the Profile via the related name
        profile = getattr(request.user, 'profile', None)
        if not profile:
            return False
            
        return profile.subscription_tier in ['pro', 'premium']

class RequiresPremiumTier(BasePermission):
    """
    Allows access only to users with a 'premium' subscription tier.
    """
    message = "You must upgrade to the Premium Career Agent tier to access this feature."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        profile = getattr(request.user, 'profile', None)
        if not profile:
            return False
            
        return profile.subscription_tier == 'premium'
