# Sample data for the Task 12 tracker.  Run with:  python manage.py shell < scripts/seed_tasks.py
import datetime

from django.contrib.auth import get_user_model
from django.utils import timezone

from tracker.models import Task

User = get_user_model()
today = timezone.localdate()
d = datetime.timedelta
student = User.objects.get(username="student")
admin = User.objects.get(username="admin")
Task.objects.bulk_create([
    Task(title="Finish Lab 07 report", description="Screenshots, tables and review answers.",
         priority="high", status="doing", due_date=today + d(days=2), owner=student),
    Task(title="Read the CBV documentation", priority="medium", due_date=today + d(days=5), owner=student),
    Task(title="Revise ORM queries", description="Q objects and lookups from Week 5.",
         priority="low", due_date=today - d(days=1), owner=student),
    Task(title="Submit Lab 06", priority="high", status="done", due_date=today - d(days=7), owner=student),
    Task(title="Grade Lab 07 submissions", priority="high", due_date=today + d(days=7), owner=admin),
])
print(Task.objects.count())
