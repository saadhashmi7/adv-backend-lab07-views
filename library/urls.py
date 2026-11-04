from django.urls import path

from . import views

app_name = "library"

urlpatterns = [
    path("debug/request/", views.request_info, name="request-info"),
    path("demo/text/", views.demo_text, name="demo-text"),
    path("demo/json/", views.demo_json, name="demo-json"),
    path("demo/redirect/", views.demo_redirect, name="demo-redirect"),
    path("demo/status/<int:code>/", views.demo_status, name="demo-status"),
]
