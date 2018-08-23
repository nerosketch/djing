import binascii
import re
import socket
from abc import ABCMeta
from hashlib import md5
from ipaddress import _BaseAddress, ip_address
from typing import Iterable, Optional, Tuple, Generator, Dict

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from djing.lib.decorators import LazyInitMetaclass
from nas_app.nas_managers.core import BaseTransmitter, NasNetworkError, NasFailedResult
from nas_app.nas_managers.structs import TariffStruct, AbonStruct, VectorAbon, VectorTariff

DEBUG = getattr(settings, 'DEBUG', False)

LIST_USERS_ALLOWED = 'DjingUsersAllowed'
LIST_DEVICES_ALLOWED = 'DjingDevicesAllowed'


class ApiRos(object):
    """Routeros api"""
    sk = None
    is_login = False

    def __init__(self, ip: str, port: int):
        if self.sk is None:
            sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sk.connect((ip, port or 8728))
            self.sk = sk

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

    def __del__(self):
        sk = getattr(self, 'sk')
        if sk is not None:
            self.sk.close()


class MikrotikTransmitter(BaseTransmitter, ApiRos, metaclass=type('_ABC_Lazy_mcs', (ABCMeta, LazyInitMetaclass), {})):
    description = _('Mikrotik NAS')

    def __init__(self, login: str, password: str, ip: str, port: int, *args, **kwargs):
        try:
            BaseTransmitter.__init__(self,
                                     login=login, password=password, ip=ip,
                                     port=port, *args, **kwargs
                                     )
            ApiRos.__init__(self, ip, port)
            self.login(username=login, pwd=password)
        except ConnectionRefusedError:
            raise NasNetworkError('Connection to %s is Refused' % ip)

    def _exec_cmd(self, cmd: Iterable) -> Dict:
        if not isinstance(cmd, (list, tuple)):
            raise TypeError
        r = dict()
        for k, v in self.talk_iter(cmd):
            if k == '!done':
                break
            elif k == '!trap':
                raise NasFailedResult(v.get('=message'))
            r[k] = v or None
        return r

    def _exec_cmd_iter(self, cmd: Iterable) -> Generator:
        if not isinstance(cmd, (list, tuple)):
            raise TypeError
        for k, v in self.talk_iter(cmd):
            if k == '!done':
                break
            elif k == '!trap':
                raise NasFailedResult(v.get('=message'))
            if v:
                yield v

    @staticmethod
    def _build_shape_obj(info: Dict) -> AbonStruct:
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
            disabled = info.get('=disabled', False)
            if disabled is not None:
                disabled = True if disabled == 'true' else False
            if target is not None and name is not None:
                # target may be '192.168.0.3/32,192.168.0.2/32'
                ips = (ip.split('/')[0] for ip in target.split(','))
                a = AbonStruct(
                    uid=int(name[3:]),
                    ips=ips,
                    tariff=t,
                    is_access=not disabled
                )
                if len(a.ips) < 1:
                    return
                a.queue_id = info.get('=.id')
                return a
        except ValueError as e:
            print('ValueError:', e)

    #################################################
    #                    QUEUES
    #################################################

    # Find queue by name
    def find_queue(self, name: str) -> Optional[AbonStruct]:
        r = self._exec_cmd(('/queue/simple/print', '?name=%s' % name))
        if r:
            return self._build_shape_obj(r.get('!re'))

    def add_queue(self, user: AbonStruct) -> None:
        if not isinstance(user, AbonStruct):
            raise TypeError
        if user.tariff is None or not isinstance(user.tariff, TariffStruct):
            return
        ips = ','.join(str(i) for i in user.ips)
        self._exec_cmd((
            '/queue/simple/add',
            '=name=uid%d' % user.uid,
            # FIXME: тут в разных микротиках или =target-addresses или =target
            '=target=%s' % ips,
            '=max-limit=%.3fM/%.3fM' % (user.tariff.speedOut, user.tariff.speedIn),
            '=queue=MikroBILL_SFQ/MikroBILL_SFQ',
            '=burst-time=1/1'
        ))

    def remove_queue(self, user: AbonStruct, queue: AbonStruct = None) -> None:
        if not isinstance(user, AbonStruct):
            raise TypeError
        if queue is None:
            queue = self.find_queue('uid%d' % user.uid)
        if queue is not None:
            queue_id = getattr(queue, 'queue_id')
            if queue_id is not None:
                self._exec_cmd((
                    '/queue/simple/remove',
                    '=.id=%s' % queue_id
                ))

    def remove_queue_range(self, q_ids: Iterable[str]):
        self._exec_cmd(('/queue/simple/remove', '=numbers=' + ','.join(q_ids)))

    def update_queue(self, user: AbonStruct, queue=None):
        if not isinstance(user, AbonStruct):
            raise TypeError
        if user.tariff is None:
            return
        if queue is None:
            queue = self.find_queue('uid%d' % user.uid)
        if queue is None:
            return self.add_queue(user)
        else:
            mk_id = getattr(queue, 'queue_id')
            cmd = [
                '/queue/simple/set',
                '=name=uid%d' % user.uid,
                '=max-limit=%.3fM/%.3fM' % (user.tariff.speedOut, user.tariff.speedIn),
                # FIXME: тут в разных версиях прошивки микротика или =target-addresses или =target
                '=target=%s' % ','.join(str(i) for i in user.ips),
                '=queue=MikroBILL_SFQ/MikroBILL_SFQ',
                '=burst-time=1/1'
            ]
            if mk_id is not None:
                cmd.insert(1, '=.id=%s' % mk_id)
            r = self._exec_cmd(cmd)
            return r

    def read_queue_iter(self) -> Generator:
        for dat in self._exec_cmd_iter(('/queue/simple/print', '=detail')):
            sobj = self._build_shape_obj(dat)
            if sobj is not None:
                yield sobj

    #################################################
    #         Ip->firewall->address list
    #################################################

    def add_ip(self, list_name: str, ip):
        if not issubclass(ip.__class__, _BaseAddress):
            raise TypeError
        commands = (
            '/ip/firewall/address-list/add',
            '=list=%s' % list_name,
            '=address=%s' % ip
        )
        return self._exec_cmd(commands)

    def remove_ip(self, mk_id):
        return self._exec_cmd((
            '/ip/firewall/address-list/remove',
            '=.id=%s' % mk_id
        ))

    def remove_ip_range(self, ip_firewall_ids: Iterable[str]):
        return self._exec_cmd((
            '/ip/firewall/address-list/remove',
            '=numbers=%s' % ','.join(ip_firewall_ids)
        ))

    def find_ip(self, ip, list_name: str):
        if not issubclass(ip.__class__, _BaseAddress):
            raise TypeError
        r = self._exec_cmd((
            '/ip/firewall/address-list/print', 'where',
            '?list=%s' % list_name,
            '?address=%s' % ip
        ))
        return r.get('!re')

    def read_ips_iter(self, list_name: str) -> Generator:
        ips = self._exec_cmd_iter((
            '/ip/firewall/address-list/print', 'where',
            '?list=%s' % list_name,
            '?dynamic=no'
        ))
        for dat in ips:
            yield ip_address(dat.get('=address')), dat.get('=.id')

    #################################################
    #         BaseTransmitter implementation
    #################################################

    def add_user_range(self, user_list: VectorAbon):
        for usr in user_list:
            self.add_user(usr)

    def remove_user_range(self, users: VectorAbon):
        if not isinstance(users, (tuple, list, set)):
            raise ValueError('*users* is used twice, generator does not fit')
        queue_ids = (usr.queue_id for usr in users if usr is not None)
        self.remove_queue_range(queue_ids)
        for user in users:
            if isinstance(user, AbonStruct):
                for ip in user.ips:
                    ip_list_entity = self.find_ip(ip, LIST_USERS_ALLOWED)
                    if ip_list_entity:
                        self.remove_ip(ip_list_entity.get('=.id'))

    def add_user(self, user: AbonStruct, *args):
        if user.tariff is None:
            return
        if not isinstance(user.tariff, TariffStruct):
            raise TypeError
        self.add_queue(user)
        for ip in user.ips:
            if not issubclass(ip.__class__, _BaseAddress):
                raise TypeError
            self.add_ip(LIST_USERS_ALLOWED, ip)

    def remove_user(self, user: AbonStruct):
        self.remove_queue(user)

        def _finder(ips):
            for ip in ips:
                r = self.find_ip(ip, LIST_USERS_ALLOWED)
                if r: yield r.get('=.id')

        firewall_ip_list_ids = _finder(user.ips)
        self.remove_ip_range(firewall_ip_list_ids)

    def update_user(self, user: AbonStruct, *args):
        # queue is instance of AbonStruct
        queue = self.find_queue('uid%d' % user.uid)
        for ip in user.ips:
            if not issubclass(ip.__class__, _BaseAddress):
                raise TypeError
            nas_ip = self.find_ip(ip, LIST_USERS_ALLOWED)
            if user.is_access:
                if nas_ip is None:
                    self.add_ip(LIST_USERS_ALLOWED, ip)
            else:
                # если не активен - то и обновлять не надо
                # но и выключить на всяк случай надо, а то вдруг был включён
                if nas_ip:
                    # и если найден был - то удалим ip из разрешённых
                    self.remove_ip(nas_ip.get('=.id'))
                if queue is not None:
                    self.remove_queue(user, queue)
                queue = None

        # если нет услуги то её не должно быть и в nas
        if user.tariff is None:
            if queue is not None:
                self.remove_queue(user, queue)
            return
        if not user.is_access:
            return

        # Проверяем шейпер
        if queue is None:
            self.add_queue(user)
            return
        if queue != user:
            self.update_queue(user, queue)

    def ping(self, host, count=10) -> Optional[Tuple[int, int]]:
        r = self._exec_cmd((
            '/ip/arp/print',
            '?address=%s' % host
        ))
        if r == {}:
            return
        interface = r['!re'].get('=interface')
        r = self._exec_cmd((
            '/ping', '=address=%s' % host, '=arp-ping=yes', '=interval=100ms', '=count=%d' % count,
            '=interface=%s' % interface
        ))
        res = r.get('!re')
        if res is not None:
            received, sent = int(res.get('=received')), int(res.get('=sent'))
            return received, sent

    def add_tariff_range(self, tariff_list: VectorTariff):
        pass

    def remove_tariff_range(self, tariff_list: VectorTariff):
        pass

    def add_tariff(self, tariff: TariffStruct):
        pass

    def update_tariff(self, tariff: TariffStruct):
        pass

    def remove_tariff(self, tid: int):
        pass

    def read_users(self) -> VectorAbon:
        all_ips = set(ip for ip, mkid in self.read_ips_iter(LIST_USERS_ALLOWED))
        queues = (q for q in self.read_queue_iter() if all_ips.issuperset(q.ips))
        return queues

    def lease_free(self, user: AbonStruct, lease):
        queue = self.find_queue('uid%d' % user.uid)
        if len(queue.ips) > 1:
            if queue is not None:
                user.ips = tuple(i for i in user.ips if i != lease)
                self.update_queue(user, queue)
            ip = self.find_ip(lease, LIST_USERS_ALLOWED)
            if ip is not None:
                self.remove_ip(ip.get('=.id'))
        else:
            raise NasFailedResult(_('You cannot disable last session'))

    def lease_start(self, user: AbonStruct, lease):
        if not issubclass(lease.__class__, _BaseAddress):
            lease = ip_address(lease)
        if not isinstance(user, AbonStruct):
            raise TypeError
        ip = self.find_ip(lease, LIST_USERS_ALLOWED)
        if ip is None:
            self.add_ip(LIST_USERS_ALLOWED, lease)
        queue = self.find_queue('uid%d' % user.uid)
        user.ips += lease,
        if queue is None:
            self.add_queue(user)
        else:
            self.update_queue(user, queue)
