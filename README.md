# Campus Library – Lab 07: Implementing Views in Django

Advanced Back-End Development (CS02338|11) · BS Information Engineering Technology · The University of Lahore · Fall 2026

A small Django 5.2 project that implements the same library features as
**function-based views (FBVs)** and **class-based views (CBVs)**, plus a JSON API,
a debugging module with eight fixed bugs (Task 11) and the take-home **tracker** app (Task 12).

## Run it

```bash
# inside CampusLibrary/
python -m venv venv
venv\Scripts\activate              # Windows (PowerShell / Command Prompt)
source venv/bin/activate           # macOS / Linux

pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser                 # e.g. admin
python manage.py shell < scripts/seed_books.py   # the 7 seed books (Emma = borrowed)
python manage.py shell -c "from django.contrib.auth import get_user_model; get_user_model().objects.create_user('student', password='Lab07-pass!')"
python manage.py shell < scripts/seed_tasks.py   # optional: sample tracker tasks (needs users admin + student)
python manage.py runserver                       # http://127.0.0.1:8000/library/
```

> Windows PowerShell does not support `<` redirection. Use
> `Get-Content scripts\seed_books.py | python manage.py shell` instead (or Command Prompt / Git Bash).

The submission ZIP also contains a ready `db.sqlite3` (7 books, sample tasks) with these demo accounts:

| Username | Password | Role |
|---|---|---|
| `admin` | `Admin07-pass!` | superuser / staff |
| `student` | `Lab07-pass!` | normal user (non-staff) |

## Useful commands

| Command | Purpose |
|---|---|
| `python manage.py check` | configuration / URL checks (`System check identified no issues`) |
| `python manage.py test` | 42 automated tests (`library/tests.py` 26, `tracker/tests.py` 16) |
| `python manage.py showmigrations` | `library.0001_initial`, `tracker.0001_initial` applied |

## URL map

All library routes are under `/library/` (namespace `library`).

| Route | View | Style / notes | Task |
|---|---|---|---|
| `""` | `home` | FBV, template | 3 |
| `debug/request/` | `request_info` | FBV, plain text | 1 |
| `demo/text/` · `demo/json/` · `demo/redirect/` | `demo_text` · `demo_json` · `demo_redirect` | FBV response types | 2 |
| `demo/status/<int:code>/` | `demo_status` | FBV, custom status (400 outside 200–599) | 2 |
| `books/` | `book_list` | FBV, search + filter | 3, 7 |
| `books/add/` | `add_book` | FBV, GET + POST, validation, PRG, login required | 4, 6, 7 |
| `books/<int:pk>/` | `book_detail` | FBV, `get_object_or_404` | 3 |
| `books/<int:pk>/borrow/` | `toggle_borrow` | FBV, POST only, login required | 5, 6 |
| `books/<int:pk>/delete/` | `delete_book` | FBV, GET confirm + POST delete, login required | 5, 6 |
| `cbv/manual/books/` · `cbv/manual/books/add/` | `BookListBaseView` · `BookCreateManualView` | CBV from `View` | 7 |
| `cbv/books/` | `BookListView` | `ListView` + pagination (3/page) + `TimedMixin` | 8, 9 |
| `cbv/books/<int:pk>/` | `BookDetailView` | `DetailView` | 8 |
| `cbv/books/add/` | `BookCreateView` | `CreateView` + `LoginRequiredMixin` | 8 |
| `cbv/books/<int:pk>/edit/` | `BookUpdateView` | `UpdateView` | 8 |
| `cbv/books/<int:pk>/delete/` | `BookDeleteView` | `DeleteView`, **staff only** (`StaffRequiredMixin`) | 8, 9 |
| `cbv/books/<int:pk>/borrow/` | `BorrowToggleView` | CBV from `View`, POST only | 7 |
| `api/books/` | `BookApiView` | CBV, JSON GET + POST (401/400/201/405 as JSON) | 10 |
| `api/books/<int:pk>/` | `api_book_detail` | FBV, JSON, 404 as JSON, GET only | 10 |

Other mounts: `/admin/`, `/accounts/` (`django.contrib.auth.urls`: login, logout, …),
`/buggy/` (Task 11 debug module, namespace `buggy`), `/tracker/` (Task 12, namespace `tracker`).

### Tracker (`/tracker/`, Task 12)

| Route | View | Style |
|---|---|---|
| `""` | `task_list` | FBV – current user's tasks, `?q=` search, `?status=` filter, counts |
| `add/` | `TaskCreateView` | `CreateView` – owner set in `form_valid` |
| `<int:pk>/` | `TaskDetailView` | `DetailView` – `get_queryset` limited to owner (others → 404) |
| `<int:pk>/edit/` | `TaskUpdateView` | `UpdateView` + `OwnerOnlyMixin` (others → 403) |
| `<int:pk>/delete/` | `TaskDeleteView` | `DeleteView` + `OwnerOnlyMixin` |
| `<int:pk>/toggle/` | `toggle_done` | FBV, POST only (Done / Reopen) |
| `api/tasks/` | `api_tasks` | FBV, JSON (401 JSON when anonymous) |

## Where things are

| Path | Contents |
|---|---|
| `config/` | settings (`library`, `tracker` in `INSTALLED_APPS`; `LOGIN_URL` etc.), root URLconf |
| `library/models.py` | `Book` (title, author, published_year, status, created_at; `get_absolute_url`) |
| `library/views.py` | all FBVs and CBVs of Tasks 1–10, helpers `filter_books` / `validate_book_form`, mixins |
| `library/urls.py` | namespaced URLconf (`app_name = "library"`) |
| `library/templates/library/` | `base`, `home`, `book_list`, `book_detail`, `add_book`, `book_confirm_delete`, `cbv_book_list`, `book_form`, `buggy_add` |
| `library/templates/registration/login.html` | login page for `django.contrib.auth` views |
| `library/views_buggy.py`, `library/urls_buggy.py` | Task 11 debug module, **fixed** (each fix marked `FIX n`) |
| `task11_buggy_original/` | the eight-bug originals, for comparison only (never imported) |
| `tracker/` | Task 12 app: model, views, URLs, templates, migrations, tests |
| `scripts/` | `seed_books.py`, `seed_tasks.py` |
