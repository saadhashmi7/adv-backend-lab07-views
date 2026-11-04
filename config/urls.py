"""Root URLconf for the Campus Library project (Lab 07)."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("library/", include("library.urls")),
]
