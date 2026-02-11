from rest_framework import permissions

class IsAgentOrSellerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow agents and sellers to create/edit properties.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to agents and sellers
        return (request.user and request.user.is_authenticated and 
                request.user.role in ['agent', 'seller'])

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are allowed to:
        # 1. The owner of the property
        # 2. The managing agent of the property
        return (obj.owner == request.user or 
                (obj.agent and obj.agent == request.user))

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object
        return obj.user == request.user 