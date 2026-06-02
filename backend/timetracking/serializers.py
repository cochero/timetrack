from rest_framework import serializers
from .models import TimeEntry


class TimeEntrySerializer(serializers.ModelSerializer):
    hours = serializers.FloatField(read_only=True)
    activity_label = serializers.CharField(source="get_activity_type_display", read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True, default=None)
    client_name = serializers.CharField(source="client.name", read_only=True, default=None)

    class Meta:
        model = TimeEntry
        fields = [
            "id", "user", "activity_type", "activity_label", "project", "project_name",
            "client", "client_name", "entry_date", "minutes", "hours",
            "description", "is_billable", "status", "timesheet", "created_at",
        ]
        read_only_fields = ["id", "user", "status", "hours", "activity_label",
                            "project_name", "client_name", "created_at"]

    def validate(self, attrs):
        request = self.context["request"]
        org = request.user.organization_id
        atype = attrs.get("activity_type", getattr(self.instance, "activity_type", "WORK"))
        project = attrs.get("project")
        client = attrs.get("client")

        if project and project.organization_id != org:
            raise serializers.ValidationError("Project is not in your organization.")
        if client and client.organization_id != org:
            raise serializers.ValidationError("Client is not in your organization.")
        if attrs.get("minutes", 0) > 24 * 60:
            raise serializers.ValidationError("More than 24 hours in one entry.")

        if atype == "WORK" and not project:
            raise serializers.ValidationError("Project work needs a project.")
        if atype == "CLIENT_MEETING" and not client:
            raise serializers.ValidationError("A client meeting needs a client.")
        if atype in ("BREAK", "INTERNAL_MEETING") and (project or client):
            raise serializers.ValidationError("Breaks and internal meetings have no project or client.")
        if atype in ("INTERNAL_MEETING", "CLIENT_MEETING") and not str(attrs.get("description", "")).strip():
            raise serializers.ValidationError("Please add a short description for the meeting.")
        return attrs
