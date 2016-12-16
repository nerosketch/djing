from django.contrib.auth.models import AnonymousUser

from taskapp.models import Task


def get_active_tasks_count(request):
    tasks_count = 0
    if not isinstance(request.user, AnonymousUser):
        tasks_count = Task.objects.filter(recipients=request.user, state='S').count()
    return {
        'tasks_count': tasks_count
    }
