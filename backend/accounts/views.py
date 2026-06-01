from rest_framework import generics, permissions, viewsets
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from common.viewsets import OrgScopedModelViewSet
from common.permissions import IsAuthenticatedInOrg, IsManager
from .models import User
from .serializers import RegisterOrgSerializer, UserSerializer, ManageUserSerializer


class RegisterOrgView(generics.CreateAPIView):
    """Public endpoint: a new firm signs up here."""
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterOrgSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=201)


class MeView(generics.RetrieveAPIView):
    """Returns the currently logged-in user's profile."""
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class UserViewSet(OrgScopedModelViewSet):
    """
    Managers add and manage their firm's employees here.
    Deleting an employee deactivates them (it never erases their logged time).
    """
    serializer_class = ManageUserSerializer
    permission_classes = [IsAuthenticatedInOrg, IsManager]
    queryset = User.objects.all()

    def get_queryset(self):
        return super().get_queryset().order_by("full_name", "email")

    def perform_destroy(self, instance):
        if instance.pk == self.request.user.pk:
            raise ValidationError("You can't deactivate your own account.")
        instance.is_active = False
        instance.save(update_fields=["is_active"])


class OrgView(generics.RetrieveUpdateAPIView):
    """Read the firm's settings; managers can update (e.g. idle timeout)."""
    serializer_class = ManageUserSerializer  # placeholder, replaced below
    permission_classes = [IsAuthenticatedInOrg]

    def get_object(self):
        return self.request.user.organization

    def get_serializer_class(self):
        from .serializers import OrganizationSerializer
        return OrganizationSerializer

    def update(self, request, *args, **kwargs):
        from common.permissions import MANAGER_ROLES
        from rest_framework.exceptions import PermissionDenied
        if request.user.role not in MANAGER_ROLES:
            raise PermissionDenied("Only managers can change firm settings.")
        return super().update(request, *args, **kwargs)
