from rest_framework import serializers
from .models import TimeEntry


class TimeEntrySerializer(serializers.ModelSerializer):
    hours = serializers.FloatField(read_only=True)

    class Meta:
        model = TimeEntry
        fields = [
            "id", "user", "project", "client", "entry_date", "minutes", "hours",
            "description", "is_billable", "status", "timesheet", "created_at",
        ]
        read_only_fields = ["id", "user", "client", "status", "hours", "created_at"]

    def validate(self, attrs):
        request = self.context["request"]
        project = attrs.get("project")
        if project and project.organization_id != request.user.organization_id:
            raise serializers.ValidationError("Project is not in your organization")
        if attrs.get("minutes", 0) > 24 * 60:
            raise serializers.ValidationError("More than 24 hours in one entry")
        return attrs
