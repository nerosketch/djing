#!/usr/bin/env python3
import os, signal
from pid.decorator import pidfile
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djing.settings")
django.setup()
from messaging.sms import SmsSubmit, SmsDeliver
import re
import asterisk.manager
from time import sleep
from dialing_app.models import SMSModel, SMSOut
from django.conf import settings

ASTERISK_MANAGER_AUTH = getattr(settings, 'ASTERISK_MANAGER_AUTH', {
    'username': 'admin',
    'password': 'admin',
    'host': '127.0.0.1'
})

outbox_messages = False


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

    def send_sms(self, dev, recipient, utext):
        if not validate_tel(recipient):
            print("Tel %s is not valid" % recipient)
            return
        sms = SmsSubmit(recipient, utext)
        for pdu in sms.to_pdu():
            response = self.command('dongle pdu %s %s' % (dev, pdu.pdu))
            print(response.data)

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

    def send_from_outbox(self):
        messages = SMSOut.objects.filter(status='nw')
        for msg in messages:
            if self.send_sms(dev='sim_8318999', recipient=msg.dst, utext=msg.text):
                msg.status = 'st'
            else:
                msg.status = 'fd'
            msg.save(update_fields=['status'])


manager = MyAstManager()


def validate_tel(tel, reg=re.compile(r'^\+7978\d{7}$')):
    return bool(re.match(reg, tel))


def handle_shutdown(event, manager):
    print("Recieved shutdown event")
    manager.close()
    # we could analize the event and reconnect here


def signal_handler(signum, frame):
    if signum != 10: return
    global outbox_messages
    outbox_messages = True


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


@pidfile(pidname='dialing.py.pid', piddir='/run')
def main():
    global outbox_messages
    try:
        manager.connect(ASTERISK_MANAGER_AUTH['host'])
        manager.login(ASTERISK_MANAGER_AUTH['username'], ASTERISK_MANAGER_AUTH['password'])

        # register some callbacks
        manager.register_event('Shutdown', handle_shutdown)
        manager.register_event('DongleNewCMGR', handle_inbox_long_sms_message)  # PDU Here

        # get a status report
        response = manager.status()
        print(response)

        signal.signal(signal.SIGUSR1, handler=signal_handler)

        while True:
            if outbox_messages:
                outbox_messages = False
                manager.send_from_outbox()
            sleep(5)

    except asterisk.manager.ManagerSocketException as e:
        print("Error connecting to the manager: ", e)
    except asterisk.manager.ManagerAuthException as e:
        print("Error logging in to the manager: ", e)
    except asterisk.manager.ManagerException as e:
        print("Error: ", e)
    finally:
        manager.logoff()


if __name__ == '__main__':
    main()
