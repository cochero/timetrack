from rest_framework import serializers
from .models import Client


class ClientSerializer(serializers.ModelSerializer):
    # how many projects this client has (filled in by the view, no extra queries)
    projects_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Client
        fields = [
            "id", "name", "code", "status",
            "billing_currency", "projects_count", "created_at",
        ]
        read_only_fields = ["id", "projects_count", "created_at"]
