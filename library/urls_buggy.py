"""Task 11 - URLconf for the buggy views (mounted at /buggy/)."""
from django.urls import path

from . import views_buggy as v

app_name = "buggy"

urlpatterns = [
    path("", v.index, name="index"),
    path("b1/missing-return/", v.no_return, name="b1"),
    path("b2/books/<int:pk>/", v.book_by_id, name="b2"),  # FIX 2: converter name = view parameter
    path("b3/go-to-list/", v.go_home, name="b3"),
    path("b4/add/", v.add_without_csrf, name="b4"),
    path("b5/manual-list/", v.BuggyListView.as_view(), name="b5"),  # FIX 5: .as_view()
    path("b6/books/<int:pk>/", v.detail_wrong_template, name="b6"),
    path("b7/books/<int:pk>/", v.detail_get, name="b7"),
    path("b8/books/", v.BuggyBookListView.as_view(), name="b8"),
]
