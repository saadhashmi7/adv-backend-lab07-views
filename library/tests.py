"""Automated checks for every route in the Lab 07 URL map (Tasks 0-11)."""
import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.views.generic import ListView

from .models import Book
from .views import BookDeleteView, BookListView, StaffRequiredMixin, TimedMixin

SEED = [
    ("Dune", "Frank Herbert", 1965), ("Emma", "Jane Austen", 1815),
    ("Neuromancer", "William Gibson", 1984), ("Pride and Prejudice", "Jane Austen", 1813),
    ("The Hobbit", "J. R. R. Tolkien", 1937), ("Foundation", "Isaac Asimov", 1951),
    ("Persuasion", "Jane Austen", 1817),
]


class LibraryTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        Book.objects.bulk_create([Book(title=t, author=a, published_year=y) for t, a, y in SEED])
        Book.objects.filter(title="Emma").update(status="borrowed")
        User = get_user_model()
        cls.student = User.objects.create_user("student", password="Lab07-pass!")
        cls.admin = User.objects.create_superuser("admin", "admin@example.com", "Admin07-pass!")
        cls.dune = Book.objects.get(title="Dune")
        cls.emma = Book.objects.get(title="Emma")

    def login(self, user="student"):
        self.client.login(username=user, password="Lab07-pass!" if user == "student" else "Admin07-pass!")


class Task0SeedTests(LibraryTestCase):
    def test_seven_books_emma_borrowed(self):
        self.assertEqual(Book.objects.count(), 7)
        self.assertEqual(self.emma.status, "borrowed")
        self.assertEqual(list(Book.objects.values_list("title", flat=True))[:2], ["Dune", "Emma"])  # Meta.ordering


class Task1RequestTests(LibraryTestCase):
    def test_multi_value_query_string(self):
        r = self.client.get("/library/debug/request/?q=dune&q=emma&page=2")
        self.assertEqual(r["Content-Type"], "text/plain")
        self.assertContains(r, "GET params    : {'q': ['dune', 'emma'], 'page': ['2']}")
        self.assertContains(r, "user          : AnonymousUser")

    def test_post_without_csrf_rejected_before_view(self):
        r = Client(enforce_csrf_checks=True).post("/library/debug/request/", {"a": "1"})
        self.assertEqual(r.status_code, 403)


class Task2ResponseTests(LibraryTestCase):
    def test_text_json_redirect(self):
        r = self.client.get(reverse("library:demo-text"))
        self.assertEqual((r.status_code, r["X-Lab"], r["Content-Type"]), (200, "week7", "text/plain; charset=utf-8"))
        r = self.client.get(reverse("library:demo-json"))
        self.assertEqual(r["Content-Type"], "application/json")
        self.assertEqual(r.json()["count"], 7)
        r = self.client.get(reverse("library:demo-redirect"))
        self.assertEqual((r.status_code, r["Location"]), (302, "/library/demo/text/"))

    def test_status_codes(self):
        for code, expected in [(200, 200), (204, 204), (404, 404), (418, 418), (500, 500), (150, 400), (700, 400)]:
            self.assertEqual(self.client.get(f"/library/demo/status/{code}/").status_code, expected, code)


class Task3ListDetailTests(LibraryTestCase):
    def test_home_and_list(self):
        self.assertEqual(self.client.get("/library/").context["total"], 7)
        self.assertEqual(len(self.client.get("/library/books/").context["books"]), 7)

    def test_search_and_filter(self):
        self.assertEqual(len(self.client.get("/library/books/?q=austen").context["books"]), 3)
        books = self.client.get("/library/books/?q=a&status=borrowed").context["books"]
        self.assertEqual([b.title for b in books], ["Emma"])
        self.assertEqual(len(self.client.get("/library/books/?status=hacked").context["books"]), 7)

    def test_detail_and_404(self):
        self.assertContains(self.client.get(f"/library/books/{self.dune.pk}/"), "Frank Herbert")
        self.assertEqual(self.client.get("/library/books/999/").status_code, 404)


class Task4AddBookTests(LibraryTestCase):
    def test_validation_matrix(self):
        self.login()
        url = reverse("library:book-add")
        cases = [
            ({"title": "", "author": "", "published_year": ""}, ["Title is required.", "Author is required.", "Year must be a whole number."]),
            ({"title": "Test Book", "author": "Me", "published_year": "abc"}, ["Year must be a whole number."]),
            ({"title": "Test Book", "author": "Me", "published_year": "3000"}, ["Enter a year between 1000 and 2100."]),
        ]
        for data, errors in cases:
            r = self.client.post(url, data)
            self.assertEqual(r.status_code, 200)
            self.assertEqual(sorted(r.context["errors"].values()), sorted(errors))
            self.assertEqual(r.context["values"]["title"], data["title"])  # input re-displayed
        self.assertEqual(Book.objects.count(), 7)

    def test_valid_post_redirect_get_and_message(self):
        self.login()
        r = self.client.post(reverse("library:book-add"), {"title": "Test Book", "author": "Me", "published_year": "2020"}, follow=True)
        book = Book.objects.get(title="Test Book")
        self.assertRedirects(r, f"/library/books/{book.pk}/")
        self.assertContains(r, "&quot;Test Book&quot; was added.")

    def test_csrf_enforced(self):
        c = Client(enforce_csrf_checks=True)
        c.login(username="student", password="Lab07-pass!")
        r = c.post(reverse("library:book-add"), {"title": "X", "author": "Y", "published_year": "2000"})
        self.assertEqual(r.status_code, 403)


class Task5And6MethodAndAuthTests(LibraryTestCase):
    def test_anonymous_redirected_to_login(self):
        r = self.client.get("/library/books/add/")
        self.assertRedirects(r, "/accounts/login/?next=/library/books/add/", fetch_redirect_response=False)
        r = self.client.get(f"/library/books/{self.dune.pk}/borrow/")      # login_required runs first
        self.assertEqual(r.status_code, 302)

    def test_borrow_is_post_only(self):
        self.login()
        r = self.client.get(f"/library/books/{self.dune.pk}/borrow/")
        self.assertEqual((r.status_code, r["Allow"]), (405, "POST"))
        self.client.post(f"/library/books/{self.dune.pk}/borrow/")
        self.dune.refresh_from_db()
        self.assertEqual(self.dune.status, "borrowed")

    def test_delete_confirm_then_post(self):
        self.login()
        book = Book.objects.create(title="Test Book", author="Me", published_year=2020)
        self.assertContains(self.client.get(f"/library/books/{book.pk}/delete/"), "Yes, delete")
        r = self.client.post(f"/library/books/{book.pk}/delete/")
        self.assertRedirects(r, "/library/books/")
        self.assertFalse(Book.objects.filter(pk=book.pk).exists())

    def test_login_logout_flow(self):
        r = self.client.post("/accounts/login/", {"username": "student", "password": "Lab07-pass!", "next": "/library/books/add/"})
        self.assertRedirects(r, "/library/books/add/")
        self.assertContains(self.client.get("/library/debug/request/"), "authenticated : True")
        r = self.client.post("/accounts/logout/")
        self.assertRedirects(r, "/library/")


class Task7ViewCBVTests(LibraryTestCase):
    def test_manual_list_matches_fbv(self):
        for qs in ["", "?q=austen", "?q=a&status=borrowed"]:
            fbv = list(self.client.get(f"/library/books/{qs}").context["books"])
            cbv = list(self.client.get(f"/library/cbv/manual/books/{qs}").context["books"])
            self.assertEqual(fbv, cbv)

    def test_head_options_and_405(self):
        self.assertEqual(self.client.head("/library/cbv/manual/books/").status_code, 200)
        r = self.client.options("/library/cbv/manual/books/")
        self.assertEqual(r["Allow"], "GET, HEAD, OPTIONS")
        self.login()
        r = self.client.get(f"/library/cbv/books/{self.dune.pk}/borrow/")
        self.assertEqual(r.status_code, 405)
        self.client.post(f"/library/cbv/books/{self.emma.pk}/borrow/")
        self.emma.refresh_from_db()
        self.assertEqual(self.emma.status, "available")

    def test_manual_add(self):
        self.assertEqual(self.client.get("/library/cbv/manual/books/add/").status_code, 302)
        self.login()
        r = self.client.post("/library/cbv/manual/books/add/", {"title": "", "author": "", "published_year": "x"})
        self.assertEqual(len(r.context["errors"]), 3)
        r = self.client.post("/library/cbv/manual/books/add/", {"title": "M", "author": "N", "published_year": "1999"})
        self.assertEqual(r.status_code, 302)


class Task8GenericCBVTests(LibraryTestCase):
    def test_pagination(self):
        r = self.client.get("/library/cbv/books/")
        self.assertEqual((len(r.context["books"]), r.context["paginator"].num_pages), (3, 3))
        self.assertEqual(len(self.client.get("/library/cbv/books/?page=3").context["books"]), 1)
        self.assertEqual(self.client.get("/library/cbv/books/?page=99").status_code, 404)
        r = self.client.get("/library/cbv/books/?q=a&page=2")
        self.assertContains(r, "?page=1&q=a&status=")

    def test_detail_default_template(self):
        r = self.client.get(f"/library/cbv/books/{self.dune.pk}/")
        self.assertTemplateUsed(r, "library/book_detail.html")

    def test_create_update_redirect_to_absolute_url(self):
        self.login()
        r = self.client.post("/library/cbv/books/add/", {"title": "G", "author": "H", "published_year": 2001})
        book = Book.objects.get(title="G")
        self.assertRedirects(r, f"/library/cbv/books/{book.pk}/")
        r = self.client.post(f"/library/cbv/books/{book.pk}/edit/",
                             {"title": "G2", "author": "H", "published_year": 2001, "status": "borrowed"})
        self.assertRedirects(r, f"/library/cbv/books/{book.pk}/")
        book.refresh_from_db()
        self.assertEqual((book.title, book.status), ("G2", "borrowed"))


class Task9MixinTests(LibraryTestCase):
    def test_mro(self):
        mro = BookListView.__mro__
        self.assertLess(mro.index(TimedMixin), mro.index(ListView))   # custom mixin runs first
        self.assertIn(StaffRequiredMixin, BookDeleteView.__mro__)

    def test_delete_staff_only(self):
        book = Book.objects.create(title="Scratch", author="X", published_year=2000)
        url = f"/library/cbv/books/{book.pk}/delete/"
        self.assertEqual(self.client.get(url).status_code, 302)          # anonymous -> login
        self.login("student")
        self.assertEqual(self.client.get(url).status_code, 403)          # logged in, not staff
        self.assertEqual(self.client.post(url).status_code, 403)
        self.login("admin")
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertRedirects(self.client.post(url), "/library/cbv/books/")
        self.assertFalse(Book.objects.filter(pk=book.pk).exists())


class Task10ApiTests(LibraryTestCase):
    def test_list_and_detail(self):
        data = self.client.get("/library/api/books/").json()
        self.assertEqual(data["count"], 7)
        data = self.client.get("/library/api/books/?status=borrowed").json()
        self.assertEqual([b["title"] for b in data["results"]], ["Emma"])
        self.assertEqual(self.client.get(f"/library/api/books/{self.dune.pk}/").json()["author"], "Frank Herbert")
        r = self.client.get("/library/api/books/999/")
        self.assertEqual((r.status_code, r["Content-Type"]), (404, "application/json"))
        self.assertEqual(self.client.post(f"/library/api/books/{self.dune.pk}/").status_code, 405)

    def post_json(self, body, raw=False):
        return self.client.post("/library/api/books/", body if raw else json.dumps(body), content_type="application/json")

    def test_post_errors_and_create(self):
        self.assertEqual(self.post_json({"title": "X"}).status_code, 401)
        self.login()
        self.assertEqual(self.post_json("not json", raw=True).json(), {"error": "Invalid JSON."})
        self.assertEqual(self.post_json([1, 2]).status_code, 400)
        r = self.post_json({"title": "", "published_year": 3000})
        self.assertEqual(set(r.json()["errors"]), {"title", "author", "published_year"})
        r = self.post_json({"title": "API Book", "author": "curl", "published_year": 2021})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r["Location"], f"/library/api/books/{r.json()['id']}/")
        r = self.client.put("/library/api/books/")
        self.assertEqual((r.status_code, r.json()["error"]), (405, "Method PUT not allowed."))


class Task11FixedBugTests(LibraryTestCase):
    def test_all_eight_routes_fixed(self):
        self.assertContains(self.client.get("/buggy/b1/missing-return/"), "There are 7 books.")
        self.assertContains(self.client.get(f"/buggy/b2/books/{self.dune.pk}/"), "Dune by Frank Herbert")
        self.assertRedirects(self.client.get("/buggy/b3/go-to-list/"), "/library/books/")
        c = Client(enforce_csrf_checks=True)
        page = c.get("/buggy/b4/add/")
        token = page.context["csrf_token"]
        self.assertContains(c.post("/buggy/b4/add/", {"title": "T", "csrfmiddlewaretoken": token}), "Would add: T")
        self.assertContains(self.client.get("/buggy/b5/manual-list/"), "Books: Dune")
        self.assertEqual(self.client.get(f"/buggy/b6/books/{self.dune.pk}/").status_code, 200)
        self.assertEqual(self.client.get("/buggy/b7/books/999/").status_code, 404)
        self.assertEqual(len(self.client.get("/buggy/b8/books/").context["books"]), 7)
