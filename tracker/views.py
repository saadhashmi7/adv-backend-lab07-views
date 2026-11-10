"""Task 12 - take-home mini-project: a personal task tracker built with a mix of FBVs and CBVs.

FBVs : task_list (search + filter), toggle_done (POST only), api_tasks (JSON)
CBVs : TaskDetailView, TaskCreateView, TaskUpdateView, TaskDeleteView (generic views + mixins)
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView

from .models import Task

STATUS_VALUES = [value for value, _label in Task.STATUS_CHOICES]


# ------------------------------------------------------------------ FBVs
@login_required
def task_list(request):
    """The current user's tasks, with ?q= search and ?status= filter (unknown values are ignored)."""
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    tasks = Task.objects.filter(owner=request.user)
    counts = {row["status"]: row["n"] for row in tasks.values("status").annotate(n=Count("id"))}
    if q:
        tasks = tasks.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if status in STATUS_VALUES:
        tasks = tasks.filter(status=status)
    return render(request, "tracker/task_list.html", {
        "tasks": tasks,
        "q": q,
        "status": status,
        "status_choices": Task.STATUS_CHOICES,
        "counts": [(label, counts.get(value, 0)) for value, label in Task.STATUS_CHOICES],
    })


@login_required
@require_POST
def toggle_done(request, pk):
    """Mark a task done / reopen it. POST only, owner only (other users get 404)."""
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    task.status = "todo" if task.status == "done" else "done"
    task.save(update_fields=["status"])
    messages.info(request, f'"{task.title}" is now {task.get_status_display().lower()}.')
    if request.POST.get("next") == "list":       # fixed choice, never an arbitrary URL (no open redirect)
        return redirect("tracker:task-list")
    return redirect(task)


@require_GET
def api_tasks(request):
    """JSON list of the current user's tasks; 401 as JSON for anonymous clients."""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required."}, status=401)
    tasks = Task.objects.filter(owner=request.user)
    status = request.GET.get("status", "")
    if status in STATUS_VALUES:
        tasks = tasks.filter(status=status)
    data = [{
        "id": t.pk,
        "title": t.title,
        "priority": t.priority,
        "status": t.status,
        "due_date": t.due_date.isoformat() if t.due_date else None,
        "overdue": t.is_overdue,
        "url": t.get_absolute_url(),
    } for t in tasks]
    return JsonResponse({"owner": request.user.username, "count": len(data), "results": data})


# ------------------------------------------------------------------ mixins
class OwnerOnlyMixin(UserPassesTestMixin):
    """Logged-in users who do not own the task get 403 Forbidden."""

    def test_func(self):
        return self.get_object().owner == self.request.user


# ------------------------------------------------------------------ CBVs
class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task

    def get_queryset(self):
        # hook: only the owner's tasks exist for this view -> someone else's id gives 404
        return super().get_queryset().filter(owner=self.request.user)


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    fields = ["title", "description", "priority", "due_date"]

    def form_valid(self, form):
        form.instance.owner = self.request.user          # never trust an owner field from the client
        messages.success(self.request, f'Task "{form.instance.title}" was created.')
        return super().form_valid(form)


class TaskUpdateView(LoginRequiredMixin, OwnerOnlyMixin, UpdateView):
    model = Task
    fields = ["title", "description", "priority", "status", "due_date"]

    def form_valid(self, form):
        messages.success(self.request, f'Task "{form.instance.title}" was updated.')
        return super().form_valid(form)


class TaskDeleteView(LoginRequiredMixin, OwnerOnlyMixin, DeleteView):
    model = Task
    success_url = reverse_lazy("tracker:task-list")

    def form_valid(self, form):
        messages.success(self.request, f'Task "{self.object.title}" was deleted.')
        return super().form_valid(form)
