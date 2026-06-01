from rest_framework.decorators import action
from rest_framework.response import Response

from common.viewsets import OrgScopedModelViewSet
from common.permissions import IsAuthenticatedInOrg, IsManagerOrReadOnly, MANAGER_ROLES
from clients.models import Client
from .models import Allocation
from .serializers import AllocationSerializer


class AllocationViewSet(OrgScopedModelViewSet):
    """
    Assign employees to projects/clients as DEDICATED or SHARED.
    Filters: ?user= ?project= ?client= ?type=DEDICATED|SHARED ?active=true|false
    """
    serializer_class = AllocationSerializer
    permission_classes = [IsAuthenticatedInOrg, IsManagerOrReadOnly]
    queryset = Allocation.objects.all()

    def get_queryset(self):
        qs = super().get_queryset().select_related("user", "project", "project__client")
        u = self.request.user
        # employees see only their own allocations; managers see everyone's
        if u.role not in MANAGER_ROLES:
            qs = qs.filter(user=u)
        p = self.request.query_params
        if p.get("user"):
            qs = qs.filter(user_id=p["user"])
        if p.get("project"):
            qs = qs.filter(project_id=p["project"])
        if p.get("client"):
            qs = qs.filter(project__client_id=p["client"])
        if p.get("type"):
            qs = qs.filter(allocation_type=p["type"])
        if p.get("active") in ("true", "false"):
            qs = qs.filter(is_active=(p["active"] == "true"))
        return qs

    @action(detail=False, methods=["get"])
    def matrix(self, request):
        """Employee-by-client grid of who is allocated where (managers only)."""
        u = request.user
        if u.role not in MANAGER_ROLES:
            return Response({"detail": "Managers only."}, status=403)

        org_id = u.organization_id
        clients = list(
            Client.objects.filter(organization_id=org_id, status="ACTIVE")
            .values("id", "name")
        )
        allocs = (
            Allocation.objects
            .filter(organization_id=org_id, is_active=True)
            .select_related("user", "project", "project__client")
        )

        rows = {}
        for a in allocs:
            row = rows.setdefault(a.user_id, {
                "user_id": a.user_id,
                "user_name": a.user.full_name or a.user.email,
                "cells": {},
                "total_percentage": 0,
            })
            cid = a.project.client_id
            cell = row["cells"].setdefault(cid, {"percentage": 0, "type": a.allocation_type})
            cell["percentage"] += a.allocation_percentage
            row["total_percentage"] += a.allocation_percentage

        return Response({"clients": clients, "rows": list(rows.values())})
