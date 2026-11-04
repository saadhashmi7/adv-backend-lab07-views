from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.views.decorators.http import require_http_methods, require_POST

from .models import Book


# ---------------------------------------------------------------- Task 7 helpers
def filter_books(params, queryset=None):
    """Apply ?q= and ?status= filters. Returns (books, q, status)."""
    q = params.get("q", "").strip()
    status = params.get("status", "")
    books = Book.objects.all() if queryset is None else queryset
    if q:
        books = books.filter(Q(title__icontains=q) | Q(author__icontains=q))
    if status in ("available", "borrowed"):
        books = books.filter(status=status)
    return books, q, status


def validate_book_form(data):
    """Return (values, errors, year) for submitted book form data."""
    values = {key: data.get(key, "").strip() for key in ("title", "author", "published_year")}
    errors = {}
    if not values["title"]:
        errors["title"] = "Title is required."
    if not values["author"]:
        errors["author"] = "Author is required."
    year = None
    try:
        year = int(values["published_year"])
        if not 1000 <= year <= 2100:
            errors["published_year"] = "Enter a year between 1000 and 2100."
    except ValueError:
        errors["published_year"] = "Year must be a whole number."
    return values, errors, year


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
    books, q, status = filter_books(request.GET)
    return render(request, "library/book_list.html", {"books": books, "q": q, "status": status})


def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    return render(request, "library/book_detail.html", {"book": book})


# ---------------------------------------------------------------- Task 4
@login_required
def add_book(request):
    values, errors = {"title": "", "author": "", "published_year": ""}, {}
    if request.method == "POST":
        values, errors, year = validate_book_form(request.POST)
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


# ---------------------------------------------------------------- Task 7: CBVs from View
class BookListBaseView(View):
    template_name = "library/book_list.html"

    def get(self, request):
        books, q, status = filter_books(request.GET)
        return render(request, self.template_name, {"books": books, "q": q, "status": status})


class BookCreateManualView(LoginRequiredMixin, View):
    template_name = "library/add_book.html"

    def get(self, request):
        return render(request, self.template_name, {"values": {}, "errors": {}})

    def post(self, request):
        values, errors, year = validate_book_form(request.POST)
        if errors:
            return render(request, self.template_name, {"values": values, "errors": errors})
        book = Book.objects.create(
            title=values["title"], author=values["author"], published_year=year,
        )
        messages.success(request, f'"{book.title}" was added.')
        return redirect("library:book-detail", pk=book.pk)


class BorrowToggleView(LoginRequiredMixin, View):
    def post(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        book.status = "borrowed" if book.status == "available" else "available"
        book.save(update_fields=["status"])
        messages.info(request, f'"{book.title}" is now {book.get_status_display().lower()}.')
        return redirect("library:book-detail", pk=book.pk)


# ---------------------------------------------------------------- Task 8: generic CBVs
class BookListView(ListView):
    model = Book
    template_name = "library/cbv_book_list.html"
    context_object_name = "books"
    paginate_by = 3

    def get_queryset(self):
        books, _q, _status = filter_books(self.request.GET, super().get_queryset())
        return books

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "").strip()
        context["status"] = self.request.GET.get("status", "")
        return context


class BookDetailView(DetailView):
    model = Book


class BookCreateView(LoginRequiredMixin, CreateView):
    model = Book
    fields = ["title", "author", "published_year"]

    def form_valid(self, form):
        messages.success(self.request, f'"{form.instance.title}" was added.')
        return super().form_valid(form)


class BookUpdateView(LoginRequiredMixin, UpdateView):
    model = Book
    fields = ["title", "author", "published_year", "status"]

    def form_valid(self, form):
        messages.success(self.request, f'"{form.instance.title}" was updated.')
        return super().form_valid(form)


class BookDeleteView(LoginRequiredMixin, DeleteView):
    model = Book
    success_url = reverse_lazy("library:cbv-book-list")

    def form_valid(self, form):
        messages.success(self.request, f'"{self.object.title}" was deleted.')
        return super().form_valid(form)
