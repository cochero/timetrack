from rest_framework import viewsets
from .permissions import IsAuthenticatedInOrg


class OrgScopedModelViewSet(viewsets.ModelViewSet):
    """
    Base class for every "list/create/edit/delete" API.

    It guarantees two things automatically:
      1. A user only ever sees records from their own organization.
      2. New records are stamped with the user's organization.

    This is the safety net that keeps each firm's data separate.
    """
    permission_classes = [IsAuthenticatedInOrg]

    def get_queryset(self):
        return super().get_queryset().filter(
            organization_id=self.request.user.organization_id
        )

    def perform_create(self, serializer):
        serializer.save(organization_id=self.request.user.organization_id)
