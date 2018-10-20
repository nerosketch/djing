import binascii
import re
import socket
from abc import ABCMeta
from hashlib import md5
from ipaddress import ip_network, _BaseNetwork
from typing import Iterable, Optional, Tuple, Generator, Dict, Iterator

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from djing.lib.decorators import LazyInitMetaclass
from nas_app.nas_managers import core
from nas_app.nas_managers import structs as i_structs

DEBUG = getattr(settings, 'DEBUG', False)

LIST_USERS_ALLOWED = 'DjingUsersAllowed'
LIST_DEVICES_ALLOWED = 'DjingDevicesAllowed'


class ApiRos(object):
    """Routeros api"""
    __sk = None
    is_login = False

    def __init__(self, ip: str, port: int):
        if self.__sk is None:
            sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sk.connect((ip, port or 8728))
            self.__sk = sk

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
                                 "=response=00" + binascii.hexlify(
                                     md.digest()).decode('utf-8'))):
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
            self.write_bytes(
                bytes(((l >> 16) & 0xff, (l >> 8) & 0xff, l & 0xff)))
        elif l < 0x10000000:
            l |= 0xE0000000
            self.write_bytes(bytes(((l >> 24) & 0xff, (l >> 16) & 0xff,
                                    (l >> 8) & 0xff, l & 0xff)))
        else:
            self.write_bytes(bytes((0xf0, (l >> 24) & 0xff, (l >> 16) & 0xff,
                                    (l >> 8) & 0xff, l & 0xff)))

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
            r = self.__sk.send(s[n:])
            if r == 0:
                raise core.NasFailedResult("connection closed by remote end")
            n += r

    def read_bytes(self, length):
        ret = b''
        while len(ret) < length:
            s = self.__sk.recv(length - len(ret))
            if len(s) == 0:
                raise core.NasFailedResult("connection closed by remote end")
            ret += s
        return ret

    def __del__(self):
        if self.__sk is not None:
            self.__sk.close()


class MikrotikTransmitter(core.BaseTransmitter, ApiRos,
                          metaclass=type('_ABC_Lazy_mcs',
                                         (ABCMeta, LazyInitMetaclass), {})):
    description = _('Mikrotik NAS')

    def __init__(self, login: str, password: str, ip: str, port: int, *args,
                 **kwargs):
        try:
            core.BaseTransmitter.__init__(self,
                                          login=login, password=password,
                                          ip=ip,
                                          port=port, *args, **kwargs
                                          )
            ApiRos.__init__(self, ip, port)
            self.login(username=login, pwd=password)
        except ConnectionRefusedError:
            raise core.NasNetworkError('Connection to %s is Refused' % ip)

    def _exec_cmd(self, cmd: Iterable) -> Dict:
        if not isinstance(cmd, (list, tuple)):
            raise TypeError
        r = dict()
        for k, v in self.talk_iter(cmd):
            if k == '!done':
                break
            elif k == '!trap':
                raise core.NasFailedResult(v.get('=message'))
            r[k] = v or None
        return r

    def _exec_cmd_iter(self, cmd: Iterable) -> Generator:
        if not isinstance(cmd, (list, tuple)):
            raise TypeError
        for k, v in self.talk_iter(cmd):
            if k == '!done':
                break
            elif k == '!trap':
                raise core.NasFailedResult(v.get('=message'))
            if v:
                yield v

    @staticmethod
    def _build_shape_obj(info: Dict) -> i_structs.SubnetQueue:
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
        speed_in = parse_speed(speed_in)
        speed_out = parse_speed(speed_out)
        try:
            target = info.get('=target')
            if target is None:
                target = info.get('=target-addresses')
            name = info.get('=name')
            disabled = info.get('=disabled', False)
            if disabled is not None:
                disabled = True if disabled == 'true' else False
            if target and name:
                # target may be '192.168.0.3/32,192.168.0.2/32'
                net = target.split(',')[0]
                if not net:
                    return
                a = i_structs.SubnetQueue(
                    name=name,
                    network=net,
                    max_limit=(speed_in, speed_out),
                    is_access=not disabled,
                    queue_id=info.get('=.id')
                )
                return a
        except ValueError as e:
            print('ValueError:', e)

    #################################################
    #                    QUEUES
    #################################################

    # Find queue by name
    def find_queue(self, name: str) -> Optional[i_structs.SubnetQueue]:
        r = self._exec_cmd(('/queue/simple/print', '?name=%s' % name))
        if r:
            return self._build_shape_obj(r.get('!re'))

    def add_queue(self, queue: i_structs.SubnetQueue) -> None:
        if not isinstance(queue, i_structs.SubnetQueue):
            raise TypeError('queue must be instance of SubnetQueue')
        self._exec_cmd((
            '/queue/simple/add',
            '=name=%s' % queue.name,
            # FIXME: тут в разных микротиках или =target-addresses или =target
            '=target=%s' % queue.network,
            '=max-limit=%.3fM/%.3fM' % queue.max_limit,
            '=queue=Djing_pcq/Djing_pcq',
            '=burst-time=1/1',
            '=total-queue=Djing_pcq'
        ))

    def remove_queue(self, queue: i_structs.SubnetQueue) -> None:
        if not isinstance(queue, i_structs.SubnetQueue):
            raise TypeError
        if not queue.queue_id:
            queue = self.find_queue(queue.name)
        if queue is not None:
            if queue.queue_id:
                self._exec_cmd((
                    '/queue/simple/remove',
                    '=.id=%s' % queue.queue_id
                ))

    def remove_queue_range(self, q_ids: Iterable[str]):
        ids = ','.join(q_ids)
        if len(ids) > 1:
            self._exec_cmd(('/queue/simple/remove', '=numbers=%s' % ids))

    def update_queue(self, queue: i_structs.SubnetQueue):
        if not isinstance(queue, i_structs.SubnetQueue):
            raise TypeError
        if not queue.queue_id:
            queue = self.find_queue(queue.name)
        if queue is None:
            return self.add_queue(queue)
        else:
            cmd = [
                '/queue/simple/set',
                '=name=%s' % queue.name,
                '=max-limit=%.3fM/%.3fM' % queue.max_limit,
                # FIXME: тут в разных версиях прошивки микротика
                # или =target-addresses или =target
                '=target=%s' % queue.network,
                '=queue=Djing_pcq/Djing_pcq',
                '=burst-time=1/1'
            ]
            if queue.queue_id:
                cmd.insert(1, '=.id=%s' % queue.queue_id)
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

    def add_ip(self, list_name: str, net):
        if not issubclass(net.__class__, _BaseNetwork):
            raise TypeError
        commands = (
            '/ip/firewall/address-list/add',
            '=list=%s' % list_name,
            '=address=%s' % net
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

    def find_ip(self, net, list_name: str):
        if not issubclass(net.__class__, _BaseNetwork):
            raise TypeError
        r = self._exec_cmd((
            '/ip/firewall/address-list/print', 'where',
            '?list=%s' % list_name,
            '?address=%s' % net
        ))
        return r.get('!re')

    def read_nets_iter(self, list_name: str) -> Generator:
        nets = self._exec_cmd_iter((
            '/ip/firewall/address-list/print', 'where',
            '?list=%s' % list_name,
            '?dynamic=no'
        ))
        for dat in nets:
            n = ip_network(dat.get('=address'))
            n.queue_id = dat.get('=.id')
            yield n

    #################################################
    #         BaseTransmitter implementation
    #################################################

    def add_user_range(self, queue_list: i_structs.VectorQueue):
        for q in queue_list:
            self.add_user(q)

    def remove_user_range(self, queues: i_structs.VectorQueue):
        if not isinstance(queues, (tuple, list, set)):
            raise ValueError('*users* is used twice, generator does not fit')
        queue_ids = (q.queue_id for q in queues if q)
        self.remove_queue_range(queue_ids)
        for q in queues:
            if isinstance(q, i_structs.SubnetQueue):
                ip_list_entity = self.find_ip(q.network, LIST_USERS_ALLOWED)
                if ip_list_entity:
                    self.remove_ip(ip_list_entity.get('=.id'))

    def add_user(self, queue: i_structs.SubnetQueue, *args):
        try:
            self.add_queue(queue)
        except core.NasFailedResult as e:
            print('Error:', e)
        net = queue.network
        if not issubclass(net.__class__, _BaseNetwork):
            raise TypeError
        try:
            self.add_ip(LIST_USERS_ALLOWED, net)
        except core.NasFailedResult as e:
            print('Error:', e)

    def remove_user(self, queue: i_structs.SubnetQueue):
        self.remove_queue(queue)
        r = self.find_ip(queue.network, LIST_USERS_ALLOWED)
        ip_id = r.get('=.id')
        self.remove_ip(ip_id)

    def update_user(self, queue: i_structs.SubnetQueue, *args):
        self.update_queue(queue)

    def ping(self, host, count=10) -> Optional[Tuple[int, int]]:
        r = self._exec_cmd((
            '/ip/arp/print',
            '?address=%s' % host
        ))
        if r == {}:
            return
        interface = r['!re'].get('=interface')
        r = self._exec_cmd((
            '/ping', '=address=%s' % host, '=arp-ping=yes', '=interval=100ms',
            '=count=%d' % count,
            '=interface=%s' % interface
        ))
        res = r.get('!re')
        if res is not None:
            received, sent = int(res.get('=received')), int(res.get('=sent'))
            return received, sent

    def read_users(self) -> i_structs.VectorQueue:
        return self.read_queue_iter()

    def sync_nas(self, users_from_db: Iterator):
        queues_from_db = (
            ab.build_agent_struct() for ab in users_from_db
            if ab is not None and ab.is_access()
        )
        queues_from_db = set(filter(lambda x: x is not None, queues_from_db))
        queues_from_gw = self.read_queue_iter()

        user_q_for_add, user_q_for_del = core.diff_set(queues_from_db,
                                                       set(queues_from_gw))

        self.remove_queue_range(
            (q.queue_id for q in user_q_for_del)
        )
        for q in user_q_for_add:
            self.add_queue(q)
        del user_q_for_add, user_q_for_del

        # sync ip addrs list
        db_nets = set(net.network for net in queues_from_db)
        gw_nets = set(self.read_nets_iter(LIST_USERS_ALLOWED))
        nets_add, nets_del = core.diff_set(db_nets, gw_nets)
        self.remove_ip_range(
            (q.queue_id for q in nets_del)
        )
        for q in nets_add:
            self.add_ip(LIST_USERS_ALLOWED, q)
