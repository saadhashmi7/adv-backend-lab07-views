from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Task(models.Model):
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]
    STATUS_CHOICES = [
        ("todo", "To do"),
        ("doing", "In progress"),
        ("done", "Done"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=6, choices=PRIORITY_CHOICES, default="medium")
    status = models.CharField(max_length=5, choices=STATUS_CHOICES, default="todo")
    due_date = models.DateField(null=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tasks")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["status", "due_date", "title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("tracker:task-detail", kwargs={"pk": self.pk})

    @property
    def is_overdue(self):
        return self.due_date is not None and self.status != "done" and self.due_date < timezone.localdate()
