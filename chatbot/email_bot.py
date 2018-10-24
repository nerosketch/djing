from _socket import gaierror
from smtplib import SMTPException
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.conf import settings

from chatbot.models import ChatException


def send_notify(msg_text, account, tag='none'):
    try:
        # MessageQueue.objects.push(msg=msg_text, user=account, tag=tag)
        target_email = account.email
        text_content = strip_tags(msg_text)

        msg = EmailMultiAlternatives(
            subject=getattr(settings, 'COMPANY_NAME', 'Djing notify'),
            body=text_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL'),
            to=(target_email,)
        )
        msg.attach_alternative(msg_text, 'text/html')
        msg.send()
    except SMTPException as e:
        raise ChatException('SMTPException: %s' % e)
    except gaierror as e:
        raise ChatException('Socket error: %s' % e)
