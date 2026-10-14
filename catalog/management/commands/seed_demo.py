"""Fill an empty database with a few books, a librarian and a reader, so the app has something to show."""
import datetime

from django.contrib.auth.models import Group, Permission, User
from django.core.management.base import BaseCommand

from catalog.models import Author, Book, BookInstance, Genre, Language

BOOKS = [
    ("Mary", "Shelley", (1797, 8, 30), (1851, 2, 1), "Frankenstein", "9780141439471", ["Science fiction", "Gothic"],
     "A young scientist creates a living being and spends the rest of his life with the consequences."),
    ("H. G.", "Wells", (1866, 9, 21), (1946, 8, 13), "The Time Machine", "9780141439976", ["Science fiction"],
     "A Victorian inventor travels to the year 802,701 and finds humanity split in two."),
    ("Jules", "Verne", (1828, 2, 8), (1905, 3, 24), "Twenty Thousand Leagues Under the Seas", "9780199539277",
     ["Adventure", "Science fiction"], "Captain Nemo and the Nautilus, seen through the eyes of a captured professor."),
    ("Selma", "Lagerlöf", (1858, 11, 20), (1940, 3, 16), "The Wonderful Adventures of Nils", "9781846591334",
     ["Adventure"], "A boy shrunk to the size of a thumb crosses Sweden on the back of a goose."),
]


class Command(BaseCommand):
    help = "Add demo books, copies and two users (librarian/reader, password 'demo-pass-2026')."

    def handle(self, *args, **options):
        english, _ = Language.objects.get_or_create(name="English")
        today = datetime.date.today()
        for first, last, born, died, title, isbn, genres, summary in BOOKS:
            author, _ = Author.objects.get_or_create(
                first_name=first, last_name=last,
                defaults={"date_of_birth": datetime.date(*born), "date_of_death": datetime.date(*died)})
            book, created = Book.objects.get_or_create(
                title=title, defaults={"author": author, "isbn": isbn, "summary": summary, "language": english})
            book.genre.set([Genre.objects.get_or_create(name=g)[0] for g in genres])
            if created:
                for status in ("a", "a", "o"):
                    BookInstance.objects.create(book=book, imprint="Penguin Classics", status=status,
                                                due_back=today + datetime.timedelta(days=10) if status == "o" else None)

        librarians, _ = Group.objects.get_or_create(name="Librarians")
        librarians.permissions.add(Permission.objects.get(codename="can_mark_returned"))
        for name, staff in (("librarian", True), ("reader", False)):
            if not User.objects.filter(username=name).exists():
                user = User.objects.create_user(name, password="demo-pass-2026", is_staff=staff)
                if staff:
                    user.groups.add(librarians)
        reader = User.objects.get(username="reader")
        BookInstance.objects.filter(status="o").update(borrower=reader)
        self.stdout.write(self.style.SUCCESS("Demo data ready. Log in as librarian or reader, password demo-pass-2026."))
