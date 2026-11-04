"""Task 11 - Debugging challenge (FIXED version).

This module originally contained EIGHT planted bugs (one per view / route),
each matching a row of the "Common errors and fixes" table in the lab manual.
Every fix is marked "FIX n"; the untouched originals are in
task11_buggy_original/ and in the Git history.  Mounted at /buggy/.
"""
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import ListView

from .models import Book


def index(request):
    links = [
        ("b1", None), ("b2", {"pk": 1}), ("b3", None), ("b4", None),
        ("b5", None), ("b6", {"pk": 1}), ("b7", {"pk": 999}), ("b8", None),
    ]
    items = "".join(
        f'<li><a href="{reverse("buggy:" + name, kwargs=kw)}">{name}</a></li>' for name, kw in links
    )
    return HttpResponse(f"<h1>Task 11 - buggy views</h1><ul>{items}</ul>")


# BUG 1 - ValueError: view returned None
def no_return(request):
    count = Book.objects.count()
    return HttpResponse(f"There are {count} books.")  # FIX 1: every path must return a response


# BUG 2 - TypeError: unexpected keyword argument 'id'
def book_by_id(request, pk):  # FIX 2: route now captures <int:pk> (see urls_buggy.py)
    book = Book.objects.get(pk=pk)
    return HttpResponse(f"{book.title} by {book.author}")


# BUG 3 - NoReverseMatch: name used without its namespace
def go_home(request):
    return redirect("library:book-list")  # FIX 3: "app_name:url_name"


# BUG 4 - 403 CSRF verification failed (template form had no {% csrf_token %})
def add_without_csrf(request):  # FIX 4: token added in library/buggy_add.html
    if request.method == "POST":
        title = request.POST.get("title", "").strip() or "(untitled)"
        return HttpResponse(f"Would add: {title}")
    return render(request, "library/buggy_add.html")


# BUG 5 - urls.E009 / TypeError: View.__init__() ... (class passed without .as_view())
class BuggyListView(View):  # FIX 5: urls_buggy.py now uses BuggyListView.as_view()
    def get(self, request):
        titles = ", ".join(Book.objects.values_list("title", flat=True))
        return HttpResponse(f"Books: {titles}")


# BUG 6 - TemplateDoesNotExist: library/books_detail.html
def detail_wrong_template(request, pk):
    book = get_object_or_404(Book, pk=pk)
    return render(request, "library/book_detail.html", {"book": book})  # FIX 6: correct file name


# BUG 7 - DoesNotExist -> 500 for an unknown id
def detail_get(request, pk):
    book = get_object_or_404(Book, pk=pk)  # FIX 7: 404 instead of 500
    return render(request, "library/book_detail.html", {"book": book})


# BUG 8 - page shows an empty list although rows exist
class BuggyBookListView(ListView):
    model = Book
    template_name = "library/book_list.html"
    context_object_name = "books"  # FIX 8: the template loops over "books"
