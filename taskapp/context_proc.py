from django.contrib.auth.models import AnonymousUser

from taskapp.models import Task
from accounts_app.models import UserProfile


def get_active_tasks_count(request):
    tasks_count = 0
    if isinstance(request.user, UserProfile):
        tasks_count = Task.objects.filter(recipients__in=[request.user], state='S').count()
    return {
        'tasks_count': tasks_count
    }
