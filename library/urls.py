from django.urls import path

from . import views

app_name = "library"

urlpatterns = [
    path("", views.home, name="home"),
    path("debug/request/", views.request_info, name="request-info"),
    path("demo/text/", views.demo_text, name="demo-text"),
    path("demo/json/", views.demo_json, name="demo-json"),
    path("demo/redirect/", views.demo_redirect, name="demo-redirect"),
    path("demo/status/<int:code>/", views.demo_status, name="demo-status"),
    path("books/", views.book_list, name="book-list"),
    path("books/add/", views.add_book, name="book-add"),
    path("books/<int:pk>/", views.book_detail, name="book-detail"),
    path("books/<int:pk>/borrow/", views.toggle_borrow, name="book-borrow"),
    path("books/<int:pk>/delete/", views.delete_book, name="book-delete"),
    # Task 7 - CBVs from View
    path("cbv/manual/books/", views.BookListBaseView.as_view(), name="cbv-manual-list"),
    path("cbv/manual/books/add/", views.BookCreateManualView.as_view(), name="cbv-manual-add"),
    path("cbv/books/<int:pk>/borrow/", views.BorrowToggleView.as_view(), name="cbv-book-borrow"),
    # Task 8 - generic CBVs
    path("cbv/books/", views.BookListView.as_view(), name="cbv-book-list"),
    path("cbv/books/add/", views.BookCreateView.as_view(), name="cbv-book-add"),
    path("cbv/books/<int:pk>/", views.BookDetailView.as_view(), name="cbv-book-detail"),
    path("cbv/books/<int:pk>/edit/", views.BookUpdateView.as_view(), name="cbv-book-edit"),
    path("cbv/books/<int:pk>/delete/", views.BookDeleteView.as_view(), name="cbv-book-delete"),
]
