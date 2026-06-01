from rest_framework import serializers
from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    # convenience read-only labels so the UI doesn't need extra lookups
    client_name = serializers.CharField(source="client.name", read_only=True)

    class Meta:
        model = Project
        fields = [
            "id", "client", "client_name", "name", "code",
            "project_head", "project_manager", "status",
            "is_billable", "start_date", "end_date", "created_at",
        ]
        read_only_fields = ["id", "client_name", "created_at"]

    def validate(self, attrs):
        """Make sure the client (and any assigned managers) belong to this firm."""
        request = self.context["request"]
        org_id = request.user.organization_id

        client = attrs.get("client")
        if client and client.organization_id != org_id:
            raise serializers.ValidationError("Client is not in your organization")

        for field in ("project_head", "project_manager"):
            person = attrs.get(field)
            if person and person.organization_id != org_id:
                raise serializers.ValidationError(
                    f"{field.replace('_', ' ').title()} is not in your organization"
                )
        return attrs
