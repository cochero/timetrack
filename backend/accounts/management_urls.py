from rest_framework.routers import DefaultRouter
from .views import UserViewSet, OrgView

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")

from django.urls import path
urlpatterns = router.urls + [path('org/', OrgView.as_view())]
