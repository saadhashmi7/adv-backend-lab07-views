from django.db import models
from django.urls import reverse


class Book(models.Model):
    STATUS_CHOICES = [
        ("available", "Available"),
        ("borrowed", "Borrowed"),
    ]

    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    published_year = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="available")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("library:cbv-book-detail", kwargs={"pk": self.pk})
