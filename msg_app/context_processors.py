from .models import Conversation


def get_new_messages_count(request):
    if request.user.is_anonymous():
        count = 0
    else:
        count = Conversation.objects.get_new_messages_count(request.user)
    return {'new_messages_count': count}
