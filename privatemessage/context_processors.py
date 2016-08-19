from models import PrivateMessages


def avail_messages(request):
    return {
        'avail_messages_num': PrivateMessages.objects.get_my_messages(request)
    }
