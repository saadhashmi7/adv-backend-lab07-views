from django.urls import path

from . import views

app_name = "library"

urlpatterns = [
    path("debug/request/", views.request_info, name="request-info"),
]
