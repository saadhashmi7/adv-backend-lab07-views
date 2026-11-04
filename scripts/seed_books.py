# Seed script from Task 0 Step 4 of the lab handout.
# Run with:  python manage.py shell < scripts/seed_books.py
from library.models import Book

Book.objects.bulk_create([
    Book(title="Dune", author="Frank Herbert", published_year=1965),
    Book(title="Emma", author="Jane Austen", published_year=1815),
    Book(title="Neuromancer", author="William Gibson", published_year=1984),
    Book(title="Pride and Prejudice", author="Jane Austen", published_year=1813),
    Book(title="The Hobbit", author="J. R. R. Tolkien", published_year=1937),
    Book(title="Foundation", author="Isaac Asimov", published_year=1951),
    Book(title="Persuasion", author="Jane Austen", published_year=1817),
])
Book.objects.filter(title="Emma").update(status="borrowed")
print(Book.objects.count())     # 7
