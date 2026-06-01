from rest_framework import serializers
from .models import Allocation


class AllocationSerializer(serializers.ModelSerializer):
    # read-only labels so the UI can show names without extra lookups
    user_name = serializers.SerializerMethodField()
    project_name = serializers.CharField(source="project.name", read_only=True)
    client = serializers.IntegerField(source="project.client_id", read_only=True)
    client_name = serializers.CharField(source="project.client.name", read_only=True)

    class Meta:
        model = Allocation
        fields = [
            "id", "user", "user_name", "project", "project_name",
            "client", "client_name", "allocation_type", "allocation_percentage",
            "bill_rate", "cost_rate", "start_date", "end_date",
            "is_active", "created_at",
        ]
        read_only_fields = [
            "id", "user_name", "project_name", "client", "client_name", "created_at",
        ]

    def get_user_name(self, obj):
        return obj.user.full_name or obj.user.email

    def validate(self, attrs):
        """
        Keep allocations sane:
          - employee and project must belong to this firm
          - a DEDICATED employee works for one client only
          - total active allocation for a person never exceeds 100%
        """
        request = self.context["request"]
        org_id = request.user.organization_id
        instance = self.instance  # set when editing, None when creating

        def current(field, default):
            if field in attrs:
                return attrs[field]
            return getattr(instance, field) if instance else default

        user = current("user", None)
        project = current("project", None)
        atype = current("allocation_type", Allocation.Type.SHARED)
        pct = current("allocation_percentage", 100)
        is_active = current("is_active", True)

        if user and user.organization_id != org_id:
            raise serializers.ValidationError("Employee is not in your organization")
        if project and project.organization_id != org_id:
            raise serializers.ValidationError("Project is not in your organization")
        if pct > 100:
            raise serializers.ValidationError("Allocation percentage cannot exceed 100")

        if is_active and user:
            others = Allocation.objects.filter(
                organization_id=org_id, user=user, is_active=True
            )
            if instance:
                others = others.exclude(pk=instance.pk)

            if atype == Allocation.Type.DEDICATED and others.exists():
                raise serializers.ValidationError(
                    "Dedicated means one client only, but this employee already "
                    "has other active allocations."
                )
            if others.filter(allocation_type=Allocation.Type.DEDICATED).exists():
                raise serializers.ValidationError(
                    "This employee is already dedicated to a client and cannot "
                    "take another active allocation."
                )
            total = sum(o.allocation_percentage for o in others) + pct
            if total > 100:
                raise serializers.ValidationError(
                    f"Total active allocation for this employee would be {total}%, "
                    "which is over 100%."
                )
        return attrs
