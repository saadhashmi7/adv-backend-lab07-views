from django.urls import path

from . import views

app_name = "tracker"

urlpatterns = [
    path("", views.task_list, name="task-list"),                                   # FBV
    path("add/", views.TaskCreateView.as_view(), name="task-add"),                  # CBV
    path("<int:pk>/", views.TaskDetailView.as_view(), name="task-detail"),          # CBV
    path("<int:pk>/edit/", views.TaskUpdateView.as_view(), name="task-edit"),       # CBV
    path("<int:pk>/delete/", views.TaskDeleteView.as_view(), name="task-delete"),   # CBV
    path("<int:pk>/toggle/", views.toggle_done, name="task-toggle"),                # FBV, POST only
    path("api/tasks/", views.api_tasks, name="api-tasks"),                          # FBV, JSON
]
