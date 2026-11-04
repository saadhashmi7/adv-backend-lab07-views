from django.db.models import Q
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

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
