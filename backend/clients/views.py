from django.db.models import Count

from common.viewsets import OrgScopedModelViewSet
from common.permissions import IsAuthenticatedInOrg, IsManagerOrReadOnly
from .models import Client
from .serializers import ClientSerializer


class ClientViewSet(OrgScopedModelViewSet):
    """
    Manage the firm's clients.
    Filters: ?status=ACTIVE  ?search=globex
    """
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticatedInOrg, IsManagerOrReadOnly]
    queryset = Client.objects.all()

    def get_queryset(self):
        qs = super().get_queryset().annotate(projects_count=Count("projects"))
        p = self.request.query_params
        if p.get("status"):
            qs = qs.filter(status=p["status"])
        if p.get("search"):
            qs = qs.filter(name__icontains=p["search"])
        return qs
