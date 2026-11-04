import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Task


class TrackerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.alice = User.objects.create_user("alice", password="pw-alice-1")
        cls.bob = User.objects.create_user("bob", password="pw-bob-1")
        today = timezone.localdate()
        cls.t1 = Task.objects.create(title="Write report", owner=cls.alice, priority="high",
                                     due_date=today + datetime.timedelta(days=2))
        cls.t2 = Task.objects.create(title="Old chore", owner=cls.alice, status="todo",
                                     due_date=today - datetime.timedelta(days=1))
        cls.t3 = Task.objects.create(title="Bob's task", owner=cls.bob, status="done")

    def login(self, user="alice"):
        self.client.login(username=user, password=f"pw-{user}-1")

    # --- authentication
    def test_list_requires_login(self):
        r = self.client.get(reverse("tracker:task-list"))
        self.assertRedirects(r, "/accounts/login/?next=/tracker/")

    def test_api_anonymous_gets_401_json(self):
        r = self.client.get(reverse("tracker:api-tasks"))
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json()["error"], "Authentication required.")

    # --- FBV list
    def test_list_shows_only_own_tasks(self):
        self.login()
        r = self.client.get(reverse("tracker:task-list"))
        self.assertContains(r, "Write report")
        self.assertNotContains(r, "Bob&#x27;s task")
        self.assertEqual(len(r.context["tasks"]), 2)

    def test_list_filter_and_invalid_status_ignored(self):
        self.login()
        r = self.client.get(reverse("tracker:task-list"), {"q": "report"})
        self.assertEqual([t.title for t in r.context["tasks"]], ["Write report"])
        r = self.client.get(reverse("tracker:task-list"), {"status": "hacked"})
        self.assertEqual(len(r.context["tasks"]), 2)

    def test_overdue_flag(self):
        self.assertTrue(self.t2.is_overdue)
        self.assertFalse(self.t1.is_overdue)

    # --- CBV create / detail / update / delete
    def test_create_sets_owner_and_redirects_to_detail(self):
        self.login()
        r = self.client.post(reverse("tracker:task-add"), {"title": "New", "priority": "low"})
        task = Task.objects.get(title="New")
        self.assertEqual(task.owner, self.alice)
        self.assertRedirects(r, task.get_absolute_url())

    def test_create_invalid_rerenders_with_errors(self):
        self.login()
        r = self.client.post(reverse("tracker:task-add"), {"title": "", "priority": "urgent"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("title", r.context["form"].errors)
        self.assertIn("priority", r.context["form"].errors)

    def test_detail_of_other_users_task_is_404(self):
        self.login()
        r = self.client.get(reverse("tracker:task-detail", args=[self.t3.pk]))
        self.assertEqual(r.status_code, 404)

    def test_update_by_non_owner_is_403(self):
        self.login()
        r = self.client.get(reverse("tracker:task-edit", args=[self.t3.pk]))
        self.assertEqual(r.status_code, 403)

    def test_update_by_owner(self):
        self.login()
        r = self.client.post(reverse("tracker:task-edit", args=[self.t1.pk]),
                             {"title": "Write report v2", "priority": "high", "status": "doing"})
        self.assertRedirects(r, self.t1.get_absolute_url())
        self.t1.refresh_from_db()
        self.assertEqual((self.t1.title, self.t1.status), ("Write report v2", "doing"))

    def test_delete_by_owner_and_by_other(self):
        self.login("bob")
        self.assertEqual(self.client.post(reverse("tracker:task-delete", args=[self.t1.pk])).status_code, 403)
        self.login("alice")
        r = self.client.post(reverse("tracker:task-delete", args=[self.t1.pk]))
        self.assertRedirects(r, reverse("tracker:task-list"))
        self.assertFalse(Task.objects.filter(pk=self.t1.pk).exists())

    # --- FBV toggle (POST only)
    def test_toggle_is_post_only(self):
        self.login()
        r = self.client.get(reverse("tracker:task-toggle", args=[self.t1.pk]))
        self.assertEqual(r.status_code, 405)
        self.assertEqual(r["Allow"], "POST")

    def test_toggle_flips_status(self):
        self.login()
        self.client.post(reverse("tracker:task-toggle", args=[self.t1.pk]))
        self.t1.refresh_from_db()
        self.assertEqual(self.t1.status, "done")
        r = self.client.post(reverse("tracker:task-toggle", args=[self.t1.pk]), {"next": "list"})
        self.assertRedirects(r, reverse("tracker:task-list"))
        self.t1.refresh_from_db()
        self.assertEqual(self.t1.status, "todo")

    def test_toggle_other_users_task_is_404(self):
        self.login()
        r = self.client.post(reverse("tracker:task-toggle", args=[self.t3.pk]))
        self.assertEqual(r.status_code, 404)

    # --- JSON API
    def test_api_lists_own_tasks(self):
        self.login()
        data = self.client.get(reverse("tracker:api-tasks")).json()
        self.assertEqual(data["owner"], "alice")
        self.assertEqual(data["count"], 2)
        self.assertEqual({t["title"] for t in data["results"]}, {"Write report", "Old chore"})

    def test_api_is_get_only(self):
        self.login()
        r = self.client.post(reverse("tracker:api-tasks"))
        self.assertEqual(r.status_code, 405)
