from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the snippet.
        return obj.creator == request.user


class IsAdminOrOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # we return true if the user is a super user or if he is the creator of the object
        return request.user.is_superuser or obj.creator == request.user


class IsAdminOrUser(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # we return true if the user is a super user or if he is the creator of the object
        return request.user.is_superuser or obj.id == request.user.id
