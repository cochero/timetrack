import uuid
from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers

from .models import Organization, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "email", "full_name", "employee_code",
            "role", "timezone", "is_active", "organization",
        ]
        read_only_fields = ["id", "organization"]


class RegisterOrgSerializer(serializers.Serializer):
    """Sign-up: creates the organization AND its first owner account."""
    organization_name = serializers.CharField()
    full_name = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value

    @transaction.atomic
    def create(self, data):
        base = slugify(data["organization_name"]) or "org"
        slug = base
        while Organization.objects.filter(slug=slug).exists():
            slug = f"{base}-{uuid.uuid4().hex[:6]}"
        org = Organization.objects.create(name=data["organization_name"], slug=slug)
        return User.objects.create_user(
            email=data["email"],
            password=data["password"],
            full_name=data["full_name"],
            role=User.Role.OWNER,
            organization=org,
        )


class ManageUserSerializer(serializers.ModelSerializer):
    """Used by managers to add and edit employees in their firm."""
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "employee_code", "role", "is_active", "password", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_role(self, value):
        if value == User.Role.OWNER:
            raise serializers.ValidationError("The Owner role can't be assigned here.")
        return value

    def validate_email(self, value):
        qs = User.objects.filter(email=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("That email is already in use.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        if not password:
            raise serializers.ValidationError({"password": "A starting password is required for a new employee."})
        return User.objects.create_user(password=password, **validated_data)

    def update(self, instance, validated_data):
        validated_data.pop("password", None)  # password changes happen via a separate flow
        return super().update(instance, validated_data)
