#!/usr/bin/env python3
# -*- coding: utf-8 -*
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djing.settings")
django.setup()
from messaging.sms import SmsSubmit, SmsDeliver
import re
import asterisk.manager
from time import sleep
from dialing_app.models import SMSModel
from django.conf import settings

DJING_USERNAME_PASSWORD = getattr(settings, 'DJING_USERNAME_PASSWORD', ('admin', 'admin'))


class SMS(object):
    def __init__(self, text, who, dev):
        self.text = text
        self.who = who
        self.dev = dev

    def __add__(self, other):
        if not isinstance(other, SMS):
            raise TypeError
        if self.who == other.who and self.dev == other.dev:
            self.text += other.text
        return self

    def __str__(self):
        return "%s: %s" % (self.who, self.text)


class ChunkedMsg(object):
    def __init__(self, sms_count, ref, sms):
        self.sms_count = sms_count
        self.ref = ref
        self.sms = sms


class MyAstManager(asterisk.manager.Manager):
    sms_chunks = list()

    def new_chunked_sms(self, count, ref, sms):
        msg = ChunkedMsg(count, ref, sms)
        self.sms_chunks.append(msg)

    @staticmethod
    def save_sms(sms):
        print('Inbox %s:' % sms.who, sms.text)
        if not isinstance(sms, SMS):
            raise TypeError
        SMSModel.objects.create(
            who=sms.who,
            dev=sms.dev,
            text=sms.text
        )

    def push_text(self, sms, ref, cnt):
        if not isinstance(sms, SMS):
            raise TypeError
        chunk = [c for c in self.sms_chunks if c.ref == ref]
        chunk_len = len(chunk)
        if chunk_len == 1:
            chunk = chunk[0]
            chunk.sms += sms
            if chunk.sms_count == cnt:
                self.save_sms(chunk.sms)
                self.sms_chunks.remove(chunk)

        elif chunk_len == 0:
            self.new_chunked_sms(cnt, ref, sms)



manager = MyAstManager()


def validate_tel(tel, reg=re.compile(r'^\+7978\d{7}$')):
    return bool(re.match(reg, tel))


def send_sms(dev, recipient, utext):
    if not validate_tel(recipient):
        print("Tel %s is not valid" % recipient)
        return
    sms = SmsSubmit(recipient, utext)
    for pdu in sms.to_pdu():
        response = manager.command('dongle pdu %s %s' % (dev, pdu.pdu))
        print(response.data)


def handle_shutdown(event, manager):
    print("Recieved shutdown event")
    manager.close()
    # we could analize the event and reconnect here


def handle_inbox_long_sms_message(event, manager):
    if event.has_header('Message'):
        pdu = event.get_header('Message')
        pdu = re.sub(r'^\+CMGR\:\s\d\,\,\d{1,3}\\r\\n', '', pdu)
        sd = SmsDeliver(pdu)
        data = sd.data
        chunks_count = data.get('cnt')
        sms = SMS(
            text=data.get('text'),
            who=data.get('number'),
            dev=event.get_header('Device')
        )
        if chunks_count is not None:
            # more than 1 message
            manager.push_text(sms=sms, ref=data.get('ref'), cnt=chunks_count)
        else:
            # one message
            manager.save_sms(sms)


if __name__ == '__main__':
    try:
        manager.connect('10.12.1.2')
        manager.login(*DJING_USERNAME_PASSWORD)

        # register some callbacks
        manager.register_event('Shutdown', handle_shutdown)
        manager.register_event('DongleNewCMGR', handle_inbox_long_sms_message)           # PDU Here

        # get a status report
        response = manager.status()
        print(response)
        while True:
            sleep(60)

    except asterisk.manager.ManagerSocketException as e:
        print("Error connecting to the manager: %s" % e.strerror)
    except asterisk.manager.ManagerAuthException as e:
        print("Error logging in to the manager: %s" % e.strerror)
    except asterisk.manager.ManagerException as e:
        print("Error: %s" % e.strerror)
    finally:
        manager.logoff()
