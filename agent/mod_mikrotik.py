# -*- coding: utf-8 -*-
import re
import socket
import binascii
from abc import ABCMeta
from hashlib import md5
from ipaddress import _BaseAddress
from typing import Iterable, Optional, Tuple
from django.conf import settings
from .core import NasFailedResult, NasNetworkError, BaseTransmitter
from djing.lib import Singleton
from .structs import TariffStruct, AbonStruct, VectorAbon, VectorTariff
from . import settings as local_settings
from djing import ping

DEBUG = getattr(settings, 'DEBUG', False)

LIST_USERS_ALLOWED = 'DjingUsersAllowed'
# LIST_USERS_BLOCKED = 'DjingUsersBlocked'


class ApiRos(metaclass=Singleton):
    """Routeros api"""
    sk = None
    is_login = False

    def __init__(self, ip: str, port: int):
        if self.sk is None:
            sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if port is None:
                port = local_settings.NAS_PORT
            sk.connect((ip, port or 8728))
            self.sk = sk

        self.currenttag = 0

    def login(self, username, pwd):
        if self.is_login:
            return
        chal = None
        for repl, attrs in self.talk_iter(("/login",)):
            chal = binascii.unhexlify(attrs['=ret'])
        md = md5()
        md.update(b'\x00')
        md.update(bytes(pwd, 'utf-8'))
        md.update(chal)
        for _ in self.talk_iter(("/login", "=name=" + username,
                                 "=response=00" + binascii.hexlify(md.digest()).decode('utf-8'))):
            pass
        self.is_login = True

    def talk_iter(self, words: Iterable):
        if self.write_sentence(words) == 0:
            return
        while 1:
            i = self.read_sentence()
            if len(i) == 0:
                continue
            reply = i[0]
            attrs = {}
            for w in i[1:]:
                j = w.find('=', 1)
                if j == -1:
                    attrs[w] = ''
                else:
                    attrs[w[:j]] = w[j + 1:]
            yield (reply, attrs)
            if reply == '!done':
                return

    def write_sentence(self, words: Iterable):
        ret = 0
        for w in words:
            self.write_word(w)
            ret += 1
        self.write_word('')
        return ret

    def read_sentence(self):
        r = []
        while 1:
            w = self.read_word()
            if w == '':
                return r
            r.append(w)

    def write_word(self, w):
        if DEBUG:
            print("<<< " + w)
        b = bytes(w, "utf-8")
        self.write_len(len(b))
        self.write_bytes(b)

    def read_word(self):
        ret = self.read_bytes(self.read_len()).decode('utf-8')
        if DEBUG:
            print(">>> " + ret)
        return ret

    def write_len(self, l):
        if l < 0x80:
            self.write_bytes(bytes((l,)))
        elif l < 0x4000:
            l |= 0x8000
            self.write_bytes(bytes(((l >> 8) & 0xff, l & 0xff)))
        elif l < 0x200000:
            l |= 0xC00000
            self.write_bytes(bytes(((l >> 16) & 0xff, (l >> 8) & 0xff, l & 0xff)))
        elif l < 0x10000000:
            l |= 0xE0000000
            self.write_bytes(bytes(((l >> 24) & 0xff, (l >> 16) & 0xff, (l >> 8) & 0xff, l & 0xff)))
        else:
            self.write_bytes(bytes((0xf0, (l >> 24) & 0xff, (l >> 16) & 0xff, (l >> 8) & 0xff, l & 0xff)))

    def read_len(self):
        c = self.read_bytes(1)[0]
        if (c & 0x80) == 0x00:
            pass
        elif (c & 0xC0) == 0x80:
            c &= ~0xC0
            c <<= 8
            c += self.read_bytes(1)[0]
        elif (c & 0xE0) == 0xC0:
            c &= ~0xE0
            c <<= 8
            c += self.read_bytes(1)[0]
            c <<= 8
            c += self.read_bytes(1)[0]
        elif (c & 0xF0) == 0xE0:
            c &= ~0xF0
            c <<= 8
            c += self.read_bytes(1)[0]
            c <<= 8
            c += self.read_bytes(1)[0]
            c <<= 8
            c += self.read_bytes(1)[0]
        elif (c & 0xF8) == 0xF0:
            c = self.read_bytes(1)[0]
            c <<= 8
            c += self.read_bytes(1)[0]
            c <<= 8
            c += self.read_bytes(1)[0]
            c <<= 8
            c += self.read_bytes(1)[0]
        return c

    def write_bytes(self, s):
        n = 0
        while n < len(s):
            r = self.sk.send(s[n:])
            if r == 0:
                raise NasFailedResult("connection closed by remote end")
            n += r

    def read_bytes(self, length):
        ret = b''
        while len(ret) < length:
            s = self.sk.recv(length - len(ret))
            if len(s) == 0:
                raise NasFailedResult("connection closed by remote end")
            ret += s
        return ret


class TransmitterManager(BaseTransmitter, metaclass=ABCMeta):
    def __init__(self, login=None, password=None, ip=None, port=None):
        ip = ip or getattr(local_settings, 'NAS_IP')
        if ip is None or ip == '<NAS IP>':
            raise NasNetworkError('Ip address of NAS does not specified')
        if not ping(ip):
            raise NasNetworkError('NAS %(ip_addr)s does not pinged' % {
                'ip_addr': ip
            })
        try:
            self.ar = ApiRos(ip, port)
            self.ar.login(login or getattr(local_settings, 'NAS_LOGIN'),
                          password or getattr(local_settings, 'NAS_PASSW'))
        except ConnectionRefusedError:
            raise NasNetworkError('Connection to %s is Refused' % ip)

    def __del__(self):
        if hasattr(self, 's'):
            self.s.close()

    def _exec_cmd(self, cmd: Iterable) -> list:
        if not isinstance(cmd, (list, tuple)):
            raise TypeError
        result_iter = self.ar.talk_iter(cmd)
        res = []
        for rt in result_iter:
            if rt[0] == '!trap':
                raise NasFailedResult(rt[1]['=message'])
            res.append(rt[1])
        return res

    def _exec_cmd_iter(self, cmd: Iterable) -> Iterable:
        if not isinstance(cmd, (list, tuple)):
            raise TypeError
        result_iter = self.ar.talk_iter(cmd)
        for rt in result_iter:
            if len(rt) < 2:
                continue
            if rt[0] == '!trap':
                raise NasFailedResult(rt[1]['=message'])
            yield rt

    # Build object ShapeItem from information from mikrotik
    @staticmethod
    def _build_shape_obj(info: dict) -> AbonStruct:
        # Переводим приставку скорости Mikrotik в Mbit/s
        def parse_speed(text_speed):
            text_speed_digit = float(text_speed[:-1] or 0.0)
            text_append = text_speed[-1:]
            if text_append == 'M':
                res = text_speed_digit
            elif text_append == 'k':
                res = text_speed_digit / 1000
            # elif text_append == 'G':
            #    res = text_speed_digit * 0x400
            else:
                res = float(re.sub(r'[a-zA-Z]', '', text_speed)) / 1000 ** 2
            return res

        speed_out, speed_in = info['=max-limit'].split('/')
        t = TariffStruct(
            speed_in=parse_speed(speed_in),
            speed_out=parse_speed(speed_out)
        )
        try:
            target = info.get('=target')
            if target is None:
                target = info.get('=target-addresses')
            name = info.get('=name')
            disabled = info.get('=disabled')
            if disabled is not None:
                disabled = True if disabled == 'true' else False
            if target is not None and name is not None:
                target_ip, target_net = target.split('/')
                a = AbonStruct(
                    uid=int(name[3:]),
                    ip=target_ip,
                    tariff=t,
                    is_active=disabled or False
                )
                a.queue_id = info.get('=.id')
                return a
        except ValueError:
            pass


class QueueManager(TransmitterManager, metaclass=ABCMeta):
    # Find queue by name
    def find(self, name: str) -> AbonStruct:
        ret = self._exec_cmd(('/queue/simple/print', '?name=%s' % name))
        if len(ret) > 1:
            return self._build_shape_obj(ret[0])

    def add(self, user: AbonStruct):
        if not isinstance(user, AbonStruct):
            raise TypeError
        if user.tariff is None or not isinstance(user.tariff, TariffStruct):
            return
        return self._exec_cmd(('/queue/simple/add',
                               '=name=uid%d' % user.uid,
                               # FIXME: тут в разных микротиках или =target-addresses или =target
                               '=target=%s' % user.ip,
                               '=max-limit=%.3fM/%.3fM' % (user.tariff.speedOut, user.tariff.speedIn),
                               '=queue=MikroBILL_SFQ/MikroBILL_SFQ',
                               '=burst-time=1/1'
                               ))

    def remove(self, user: AbonStruct):
        if not isinstance(user, AbonStruct):
            raise TypeError
        q = self.find('uid%d' % user.uid)
        if q is not None:
            return self._exec_cmd(('/queue/simple/remove', '=.id=' + getattr(q, 'queue_id', ''),))

    def remove_range(self, q_ids: Iterable[str]):
        try:
            # q_ids = [q.queue_id for q in q_ids]
            return self._exec_cmd(('/queue/simple/remove', '=numbers=' + ','.join(q_ids)))
        except TypeError as e:
            print(e)

    def update(self, user: AbonStruct):
        if not isinstance(user, AbonStruct):
            raise TypeError
        if user.tariff is None or not isinstance(user.tariff, TariffStruct):
            return
        queue = self.find('uid%d' % user.uid)
        if queue is None:
            return self.add(user)
        else:
            mk_id = getattr(queue, 'queue_id', '')
            return self._exec_cmd(('/queue/simple/set', '=.id=' + mk_id,
                                   '=name=uid%d' % user.uid,
                                   '=max-limit=%.3fM/%.3fM' % (user.tariff.speedOut, user.tariff.speedIn),
                                   # FIXME: тут в разных микротиках или =target-addresses или =target
                                   '=target=%s' % user.ip,
                                   '=queue=MikroBILL_SFQ/MikroBILL_SFQ',
                                   '=burst-time=1/1'
                                   ))

    def read_queue_iter(self):
        for code, dat in self._exec_cmd_iter(('/queue/simple/print', '=detail')):
            if code == '!done':
                return
            sobj = self._build_shape_obj(dat)
            if sobj is not None:
                yield sobj

    def read_mikroids_iter(self):
        queues = self._exec_cmd_iter(('/queue/simple/print', '=detail'))
        for queue in queues:
            if queue[0] == '!done':
                return
            yield int(queue[1]['=.id'].replace('*', ''), base=16)

    def disable(self, user: AbonStruct):
        if not isinstance(user, AbonStruct):
            raise TypeError
        q = self.find('uid%d' % user.uid)
        if q is None:
            self.add(user)
            return self.disable(user)
        else:
            return self._exec_cmd(('/queue/simple/disable', '=.id=*' + getattr(q, 'queue_id', '')))

    def enable(self, user: AbonStruct):
        if not isinstance(user, AbonStruct):
            raise TypeError
        q = self.find('uid%d' % user.uid)
        if q is None:
            self.add(user)
            self.enable(user)
        else:
            return self._exec_cmd(('/queue/simple/enable', '=.id=*' + getattr(q, 'queue_id', '')))


class IpAddressListManager(TransmitterManager, metaclass=ABCMeta):
    def add(self, list_name: str, ip):
        if not issubclass(ip.__class__, _BaseAddress):
            raise TypeError
        commands = (
            '/ip/firewall/address-list/add',
            '=list=%s' % list_name,
            '=address=%s' % ip
        )
        return self._exec_cmd(commands)

    def remove(self, mk_id):
        return self._exec_cmd((
            '/ip/firewall/address-list/remove',
            '=.id=%s' % mk_id
        ))

    def remove_range(self, items):
        ids = tuple(ip_mkid.mkid for ip_mkid in items)
        if len(ids) > 0:
            return self._exec_cmd([
                '/ip/firewall/address-list/remove',
                '=numbers=%s' % ','.join(ids)
            ])

    def find(self, ip, list_name: str):
        if not issubclass(ip.__class__, _BaseAddress):
            raise TypeError
        return self._exec_cmd((
            '/ip/firewall/address-list/print', 'where',
            '?list=%s' % list_name,
            '?address=%s' % ip
        ))

    def read_ips_iter(self, list_name: str):
        ips = self._exec_cmd_iter((
            '/ip/firewall/address-list/print', 'where',
            '?list=%s' % list_name,
            '?dynamic=no'
        ))
        for code, dat in ips:
            if dat != {}:
                yield dat.get('=address'), dat.get('=.id')

    def disable(self, user: AbonStruct):
        r = IpAddressListManager.find(self, user.ip, LIST_USERS_ALLOWED)
        if len(r) > 1:
            mk_id = r[0]['=.id']
            return self._exec_cmd((
                '/ip/firewall/address-list/disable',
                '=.id=' + str(mk_id),
            ))

    def enable(self, user):
        r = IpAddressListManager.find(self, user.ip, LIST_USERS_ALLOWED)
        if len(r) > 1:
            mk_id = r[0]['=.id']
            return self._exec_cmd((
                '/ip/firewall/address-list/enable',
                '=.id=' + str(mk_id),
            ))


class MikrotikTransmitter(QueueManager, IpAddressListManager):
    def add_user_range(self, user_list: VectorAbon):
        for usr in user_list:
            self.add_user(usr)

    def remove_user_range(self, users: VectorAbon):
        if not isinstance(users, (tuple, list, set)):
            raise ValueError('*users* is used twice, generator does not fit')
        queue_ids = (usr.queue_id for usr in users if usr is not None)
        QueueManager.remove_range(self, queue_ids)
        for ip in (user.ip for user in users if isinstance(user, AbonStruct)):
            ip_list_entity = IpAddressListManager.find(self, ip, LIST_USERS_ALLOWED)
            if ip_list_entity is not None and len(ip_list_entity) > 1:
                IpAddressListManager.remove(self, ip_list_entity[0]['=.id'])

    def add_user(self, user: AbonStruct, *args):
        if not issubclass(user.ip.__class__, _BaseAddress):
            raise TypeError
        if user.tariff is None:
            return
        if not isinstance(user.tariff, TariffStruct):
            raise TypeError
        try:
            QueueManager.add(self, user)
        except (NasNetworkError, NasFailedResult) as e:
            print('Error:', e)
        try:
            IpAddressListManager.add(self, LIST_USERS_ALLOWED, user.ip)
        except (NasNetworkError, NasFailedResult) as e:
            print('Error:', e)

    def remove_user(self, user: AbonStruct):
        QueueManager.remove(self, user)
        firewall_ip_list_obj = IpAddressListManager.find(self, user.ip, LIST_USERS_ALLOWED)
        if firewall_ip_list_obj is not None and len(firewall_ip_list_obj) > 1:
            IpAddressListManager.remove(self, firewall_ip_list_obj[0]['=.id'])

    def update_user(self, user: AbonStruct, *args):
        if not issubclass(user.ip.__class__, _BaseAddress):
            raise TypeError

        find_res = IpAddressListManager.find(self, user.ip, LIST_USERS_ALLOWED)
        queue = QueueManager.find(self, 'uid%d' % user.uid)

        if not user.is_active:
            # если не активен - то и обновлять не надо
            # но и выключить на всяк случай надо, а то вдруг был включён
            if len(find_res) > 1:
                # и если найден был - то удалим ip из разрешённых
                IpAddressListManager.remove(self, find_res[0]['=.id'])
            if queue is not None:
                QueueManager.remove(self, user)
            return

        # если нет услуги то её не должно быть и в nas
        if user.tariff is None or not isinstance(user.tariff, TariffStruct):
            if queue is not None:
                QueueManager.remove(self, user)
            return

        # если не найден (mikrotik возвращает пустой словарь в списке если ничего нет)
        if len(find_res) < 2:
            # добавим запись об абоненте
            IpAddressListManager.add(self, LIST_USERS_ALLOWED, user.ip)

        # Проверяем шейпер

        if queue is None:
            QueueManager.add(self, user)
            return
        if queue != user:
            QueueManager.update(self, user)

    def ping(self, host, count=10) -> Optional[Tuple[int, int]]:
        r = self._exec_cmd((
            '/ip/arp/print',
            '?address=%s' % host
        ))
        if r == [{}]:
            return
        interface = r[0]['=interface']
        r = self._exec_cmd((
            '/ping', '=address=%s' % host, '=arp-ping=yes', '=interval=100ms', '=count=%d' % count,
            '=interface=%s' % interface
        ))
        received, sent = int(r[-2:][0]['=received']), int(r[-2:][0]['=sent'])
        return received, sent

    # Тарифы хранить нам не надо, так что методы тарифов ниже не реализуем
    def add_tariff_range(self, tariff_list: VectorTariff):
        pass

    # соответственно и удалять тарифы не надо
    def remove_tariff_range(self, tariff_list: VectorTariff):
        pass

    # и добавлять тоже
    def add_tariff(self, tariff: TariffStruct):
        pass

    # и обновлять
    def update_tariff(self, tariff: TariffStruct):
        pass

    def remove_tariff(self, tid: int):
        pass

    def read_users(self) -> Iterable[AbonStruct]:

        class ip_mkid_struct(object):
            __slots__ = ('ip', 'mkid')

            def __init__(self, ip, mkid):
                self.ip = ip
                self.mkid = mkid

            def __eq__(self, other):
                if isinstance(other, ip_mkid_struct):
                    return self.ip == other.ip
                return self.ip == str(other)

            def __hash__(self):
                return hash(self.ip)

        # shapes is ShapeItem
        all_ips = set(ip_mkid_struct(ip, mkid) for ip, mkid in IpAddressListManager.read_ips_iter(self, LIST_USERS_ALLOWED))
        queues = tuple(q for q in QueueManager.read_queue_iter(self) if str(q.ip) in all_ips)

        ips_from_queues = set(str(q.ip) for q in queues)

        # delete ip addresses that are in firewall/address-list and there are no corresponding in queues
        diff = tuple(all_ips - ips_from_queues)
        if len(diff) > 0:
            IpAddressListManager.remove_range(self, diff)

        return queues
