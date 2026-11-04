"""Task 11 - Debugging challenge.

This module deliberately contains EIGHT planted bugs (one per view / route).
Each bug matches a row of the "Common errors and fixes" table in the lab
manual.  Mounted at /buggy/ by config/urls.py.
"""
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import ListView

from .models import Book


def index(request):
    links = [
        ("b1", None), ("b2", {"id": 1}), ("b3", None), ("b4", None),
        ("b5", None), ("b6", {"pk": 1}), ("b7", {"pk": 999}), ("b8", None),
    ]
    items = "".join(
        f'<li><a href="{reverse("buggy:" + name, kwargs=kw)}">{name}</a></li>' for name, kw in links
    )
    return HttpResponse(f"<h1>Task 11 - buggy views</h1><ul>{items}</ul>")


# BUG 1
def no_return(request):
    count = Book.objects.count()
    HttpResponse(f"There are {count} books.")


# BUG 2
def book_by_id(request, pk):
    book = Book.objects.get(pk=pk)
    return HttpResponse(f"{book.title} by {book.author}")


# BUG 3
def go_home(request):
    return redirect("book-list")


# BUG 4
def add_without_csrf(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip() or "(untitled)"
        return HttpResponse(f"Would add: {title}")
    return render(request, "library/buggy_add.html")


# BUG 5
class BuggyListView(View):
    def get(self, request):
        titles = ", ".join(Book.objects.values_list("title", flat=True))
        return HttpResponse(f"Books: {titles}")


# BUG 6
def detail_wrong_template(request, pk):
    book = Book.objects.filter(pk=pk).first()
    return render(request, "library/books_detail.html", {"book": book})


# BUG 7
def detail_get(request, pk):
    book = Book.objects.get(pk=pk)
    return render(request, "library/book_detail.html", {"book": book})


# BUG 8
class BuggyBookListView(ListView):
    model = Book
    template_name = "library/book_list.html"
    context_object_name = "book_list"
