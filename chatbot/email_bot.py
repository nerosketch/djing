from smtplib import SMTPException
from django.core.mail import send_mail
from django.conf import settings

from chatbot.models import ChatException, MessageQueue


def send_notify(msg_text, account, tag='none'):
    try:
        MessageQueue.objects.push(msg=msg_text, user=account, tag=tag)
        target_email = account.email
        print('send', target_email, type(target_email), 'from', getattr(settings, 'DEFAULT_FROM_EMAIL'))
        send_mail(
            subject=getattr(settings, 'COMPANY_NAME', 'Djing notify'),
            message=msg_text,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL'),
            recipient_list=(target_email,)
        )
    except SMTPException as e:
        raise ChatException('SMTPException: %s' % e)
