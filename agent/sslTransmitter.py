# -*- coding: utf-8 -*-
import ssl
import socket
from multiprocessing import Process, Manager

import settings
from models import EventNAS, Abonent, Tariff


class NetExcept(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class SSLTransmitterServer(object):
    bindsocket = None

    def connect(self, ip, port):
        self.bindsocket = socket.socket()
        self.bindsocket.bind((ip, port))
        self.bindsocket.listen(5)

    @staticmethod
    def _on_data_recive(v, data):
        print "do_something:", data
        #with lock:
        dat = EventNAS().deserialize(data)
        if dat is not None:
            v.append(dat)
        else:
            print 'ERROR: bad data:', data
        return False

    def _deal_with_client(self, connstream, v):
        data = connstream.read()
        while data:
            if not self._on_data_recive(v, data):
                break
            data = connstream.read()

    def process(self, v):
        while True:
            newsocket, fromaddr = self.bindsocket.accept()
            connstream = ssl.wrap_socket(newsocket,
                 server_side=True,
                 certfile=settings.CERTFILE,
                 keyfile=settings.KEYFILE)
            try:
                self._deal_with_client(connstream, v)
            finally:
                connstream.shutdown(socket.SHUT_RDWR)
                connstream.close()


class PlainTransmitterServer(SSLTransmitterServer):

    def process(self, v):
        while True:
            newsocket, fromaddr = self.bindsocket.accept()
            dat = newsocket.recv(0xffff)
            if not dat:
                break
            self._on_data_recive(v, dat)


# Декоратор переводит классы абонента базы к объекту агента если надо.
# abonapp.models.Abon -> agent.Abonent
def agent_abon_typer(fn):
    def wrapped(self, abon):
        if isinstance(abon, Abonent):
            fn(self, abon)
        else:
            act_tar = abon.active_tariff()
            agent_tariff = Tariff(act_tar.id, act_tar.speedIn, act_tar.speedOut) if act_tar else None
            abn = Abonent(
                abon.id,
                abon.ip_address.int_ip() if abon.ip_address else 0,
                agent_tariff,
                abon.is_active
            )
            fn(self, abn)
    return wrapped


# Декоратор переводит классы тарифа базы к объекту агента если надо.
# tariff_app.models.Tariff -> agent.Tariff
def agent_tariff_typer(fn):
    def wrapped(self, tariff):
        if isinstance(tariff, Tariff):
            fn(self, tariff)
        else:
            trf = Tariff(
                tariff.id,
                tariff.speedIn,
                tariff.speedOut
            )
            fn(self, trf)
    return wrapped


class SSLTransmitterClient(object):
    s = None

    def __init__(self, ip=None, port=None):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Require a certificate from the server. We used a self-signed certificate
            # so here ca_certs must be the server certificate itself.
            self.s = ssl.wrap_socket(s,
                ca_certs=settings.CERTFILE,
                cert_reqs=ssl.CERT_REQUIRED)
            self.s.connect((
                ip or settings.SELF_IP,
                port or settings.SELF_PORT
            ))
        except socket.error:
            raise NetExcept('Ошибка подключения к NAS агенту %s:%d' % (
                ip or settings.SELF_IP,
                port or settings.SELF_PORT
            ))

    def write(self, d):
        self.s.write(d)

    # Создаём абонента
    @agent_abon_typer
    def signal_abon_create(self, abon):
        self.write(
            EventNAS(1, abon.id, abon._serializable_obj()).serialize()
        )

    # Обновляем абонента
    @agent_abon_typer
    def signal_abon_refresh(self, abon):
        self.write(
            EventNAS(2, abon.uid, abon._serializable_obj()).serialize()
        )

    # Удаляем абонента
    @agent_abon_typer
    def signal_abon_remove(self, abon):
        self.write(
            EventNAS(3, abon.id).serialize()
        )

    # Создаём тариф
    @agent_tariff_typer
    def signal_tariff_create(self, tariff):
        self.write(
            EventNAS(4, tariff.tid, tariff._serializable_obj()).serialize()
        )

    # Обновляем тариф
    @agent_tariff_typer
    def signal_tariff_refresh(self, tariff):
        self.write(
            EventNAS(5, tariff.tid, tariff._serializable_obj()).serialize()
        )

    # Удаляем тариф
    @agent_tariff_typer
    def signal_tariff_remove(self, tariff):
        self.write(
            EventNAS(6, tariff.tid).serialize()
        )

    # Перезагружаем всё
    @agent_abon_typer
    def signal_agent_reboot(self):
        self.write(
            EventNAS(7, 0).serialize()
        )

    def __del__(self):
        if self.s:
            self.s.close()


class PlainTransmitterClient(SSLTransmitterClient):

    def __init__(self, ip=None, port=None):
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((
                ip or settings.SELF_IP,
                port or settings.SELF_PORT
            ))
        except socket.error:
            raise NetExcept(u'Ошибка подключения к NAS агенту на %s:%d' % (
                ip or settings.SELF_IP,
                port or settings.SELF_PORT
            ))

    def write(self, d):
        self.s.send(d)


# общалка с NAS'ом
def get_TransmitterClientKlass():
    if settings.IS_USE_SSL:
        return SSLTransmitterClient
    else:
        return PlainTransmitterClient


def get_TransmitterServerKlass():
    if settings.IS_USE_SSL:
        return SSLTransmitterServer
    else:
        return PlainTransmitterServer


def proc_entrypoint(obj, v, lock, ip, port):
    srv = get_TransmitterServerKlass()()
    srv.connect(ip, port)
    srv.process(v)


class TransmitServer(object):

    def __init__(self, ip, port):
        mngr = Manager()
        self.v = mngr.list()
        #self.lock = Lock()
        self.p = Process(target=proc_entrypoint, args=(self, self.v, None, ip, port))#self.lock))

    def get_data(self):
        if len(self.v) > 0:
            return list(self.v)
        else:
            return []

    def clear(self):
        del self.v[:]

    def start(self):
        self.p.start()

    def __del__(self):
        self.p.terminate()
