from common.viewsets import OrgScopedModelViewSet
from common.permissions import IsAuthenticatedInOrg, IsManagerOrReadOnly
from .models import Project
from .serializers import ProjectSerializer


class ProjectViewSet(OrgScopedModelViewSet):
    """
    Manage projects (each belongs to one client).
    Filters: ?client=<id>  ?status=ACTIVE  ?search=bookkeeping
    """
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticatedInOrg, IsManagerOrReadOnly]
    queryset = Project.objects.all()

    def get_queryset(self):
        qs = super().get_queryset().select_related("client")
        p = self.request.query_params
        if p.get("client"):
            qs = qs.filter(client_id=p["client"])
        if p.get("status"):
            qs = qs.filter(status=p["status"])
        if p.get("search"):
            qs = qs.filter(name__icontains=p["search"])
        return qs
