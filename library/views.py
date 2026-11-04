from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from .models import Book


# ---------------------------------------------------------------- Task 1
def request_info(request):
    lines = [
        f"method        : {request.method}",
        f"path          : {request.path}",
        f"full path     : {request.get_full_path()}",
        f"scheme        : {request.scheme}",
        f"host          : {request.get_host()}",
        f"GET params    : {dict(request.GET)}",
        f"POST params   : {dict(request.POST)}",
        f"content type  : {request.content_type}",
        f"user          : {request.user}",
        f"authenticated : {request.user.is_authenticated}",
        f"User-Agent    : {request.headers.get('User-Agent')}",
        f"Accept        : {request.headers.get('Accept')}",
        f"client IP     : {request.META.get('REMOTE_ADDR')}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


# ---------------------------------------------------------------- Task 2
def demo_text(request):
    response = HttpResponse("Plain text response", content_type="text/plain; charset=utf-8")
    response["X-Lab"] = "week7"
    return response


def demo_json(request):
    data = {
        "count": Book.objects.count(),
        "titles": list(Book.objects.values_list("title", flat=True)),
    }
    return JsonResponse(data)


def demo_redirect(request):
    return redirect("library:demo-text")


def demo_status(request, code):
    if not 200 <= code <= 599:
        return HttpResponseBadRequest("Use a status code between 200 and 599")
    return HttpResponse(f"Status {code}", status=code)


# ---------------------------------------------------------------- Task 3
def home(request):
    recent = Book.objects.order_by("-created_at")[:3]
    return render(request, "library/home.html", {
        "total": Book.objects.count(),
        "recent": recent,
    })


def book_list(request):
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    books = Book.objects.all()
    if q:
        books = books.filter(Q(title__icontains=q) | Q(author__icontains=q))
    if status in ("available", "borrowed"):
        books = books.filter(status=status)
    return render(request, "library/book_list.html", {
        "books": books, "q": q, "status": status,
    })


def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    return render(request, "library/book_detail.html", {"book": book})


# ---------------------------------------------------------------- Task 4
@login_required
def add_book(request):
    errors = {}
    values = {"title": "", "author": "", "published_year": ""}
    if request.method == "POST":
        values = {
            "title": request.POST.get("title", "").strip(),
            "author": request.POST.get("author", "").strip(),
            "published_year": request.POST.get("published_year", "").strip(),
        }
        if not values["title"]:
            errors["title"] = "Title is required."
        if not values["author"]:
            errors["author"] = "Author is required."
        try:
            year = int(values["published_year"])
            if not 1000 <= year <= 2100:
                errors["published_year"] = "Enter a year between 1000 and 2100."
        except ValueError:
            errors["published_year"] = "Year must be a whole number."
        if not errors:
            book = Book.objects.create(
                title=values["title"], author=values["author"], published_year=year,
            )
            messages.success(request, f'"{book.title}" was added.')
            return redirect("library:book-detail", pk=book.pk)
    return render(request, "library/add_book.html", {"values": values, "errors": errors})


# ---------------------------------------------------------------- Task 5
@login_required
@require_POST
def toggle_borrow(request, pk):
    book = get_object_or_404(Book, pk=pk)
    book.status = "borrowed" if book.status == "available" else "available"
    book.save(update_fields=["status"])
    messages.info(request, f'"{book.title}" is now {book.get_status_display().lower()}.')
    return redirect("library:book-detail", pk=book.pk)


@login_required
@require_http_methods(["GET", "POST"])
def delete_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == "POST":
        title = book.title
        book.delete()
        messages.success(request, f'"{title}" was deleted.')
        return redirect("library:book-list")
    return render(request, "library/book_confirm_delete.html", {"book": book})
