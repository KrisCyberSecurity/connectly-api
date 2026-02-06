from rest_framework.permissions import BasePermission


class IsTaskAssignee(BasePermission):
    """
    Allows access only to the user assigned to the task.
    """

    def has_object_permission(self, request, view, obj):
        return obj.assigned_to == request.user
