# -*- coding: utf-8 -*-
import socket
import binascii
from abc import ABCMeta
from hashlib import md5
from .core import BaseTransmitter, NasFailedResult, NasNetworkError
from mydefs import ping
from .structs import TariffStruct, AbonStruct, IpStruct, ShapeItem
from . import settings
from djing.settings import DEBUG
import re


#DEBUG=False

LIST_USERS_ALLOWED = 'DjingUsersAllowed'
LIST_USERS_BLOCKED = 'DjingUsersBlocked'


class ApiRos:
    "Routeros api"

    def __init__(self, sk):
        self.sk = sk
        self.currenttag = 0

    def login(self, username, pwd):
        chal = None
        for repl, attrs in self.talk_iter(["/login"]):
            chal = binascii.unhexlify(attrs['=ret'])
        md = md5()
        md.update(b'\x00')
        md.update(bytes(pwd, 'utf-8'))
        md.update(chal)
        for r in self.talk_iter(["/login", "=name=" + username,
                   "=response=00" + binascii.hexlify(md.digest()).decode('utf-8')]): pass

    def talk_iter(self, words):
        if self.writeSentence(words) == 0: return
        while 1:
            i = self.readSentence()
            if len(i) == 0: continue
            reply = i[0]
            attrs = {}
            for w in i[1:]:
                j = w.find('=', 1)
                if (j == -1):
                    attrs[w] = ''
                else:
                    attrs[w[:j]] = w[j + 1:]
            yield (reply, attrs)
            if reply == '!done': return

    def writeSentence(self, words):
        ret = 0
        for w in words:
            self.writeWord(w)
            ret += 1
        self.writeWord('')
        return ret

    def readSentence(self):
        r = []
        while 1:
            w = self.readWord()
            if w == '': return r
            r.append(w)

    def writeWord(self, w):
        if DEBUG:
            print("<<< " + w)
        b = bytes(w, "utf-8")
        self.writeLen(len(b))
        self.writeBytes(b)

    def readWord(self):
        ret = self.readBytes(self.readLen()).decode('utf-8')
        if DEBUG:
            print(">>> " + ret)
        return ret

    def writeLen(self, l):
        if l < 0x80:
            self.writeBytes(bytes([l]))
        elif l < 0x4000:
            l |= 0x8000
            self.writeBytes(bytes([(l >> 8) & 0xff, l & 0xff]))
        elif l < 0x200000:
            l |= 0xC00000
            self.writeBytes(bytes([(l >> 16) & 0xff, (l >> 8) & 0xff, l & 0xff]))
        elif l < 0x10000000:
            l |= 0xE0000000
            self.writeBytes(bytes([(l >> 24) & 0xff, (l >> 16) & 0xff, (l >> 8) & 0xff, l & 0xff]))
        else:
            self.writeBytes(bytes([0xf0, (l >> 24) & 0xff, (l >> 16) & 0xff, (l >> 8) & 0xff, l & 0xff]))

    def readLen(self):
        c = self.readBytes(1)[0]
        if (c & 0x80) == 0x00:
            pass
        elif (c & 0xC0) == 0x80:
            c &= ~0xC0
            c <<= 8
            c += self.readBytes(1)[0]
        elif (c & 0xE0) == 0xC0:
            c &= ~0xE0
            c <<= 8
            c += self.readBytes(1)[0]
            c <<= 8
            c += self.readBytes(1)[0]
        elif (c & 0xF0) == 0xE0:
            c &= ~0xF0
            c <<= 8
            c += self.readBytes(1)[0]
            c <<= 8
            c += self.readBytes(1)[0]
            c <<= 8
            c += self.readBytes(1)[0]
        elif (c & 0xF8) == 0xF0:
            c = self.readBytes(1)[0]
            c <<= 8
            c += self.readBytes(1)[0]
            c <<= 8
            c += self.readBytes(1)[0]
            c <<= 8
            c += self.readBytes(1)[0]
        return c

    def writeBytes(self, s):
        n = 0
        while n < len(s):
            r = self.sk.send(s[n:])
            if r == 0: raise RuntimeError("connection closed by remote end")
            n += r

    def readBytes(self, length):
        ret = b''
        while len(ret) < length:
            s = self.sk.recv(length - len(ret))
            if len(s) == 0: raise RuntimeError("connection closed by remote end")
            ret += s
        return ret


class TransmitterManager(BaseTransmitter, metaclass=ABCMeta):
    def __init__(self, login=None, password=None, ip=None, port=None):
        ip = ip or settings.NAS_IP
        if not ping(ip):
            raise NasNetworkError('NAS %s не пингуется' % ip)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, port or settings.NAS_PORT))
            self.s = s
            self.ar = ApiRos(s)
            self.ar.login(login or settings.NAS_LOGIN, password or settings.NAS_PASSW)
        except ConnectionRefusedError:
            raise NasNetworkError('Подключение к %s отклонено (Connection Refused)' % ip)

    def __del__(self):
        if hasattr(self, 's'):
            self.s.close()

    def _exec_cmd(self, cmd):
        assert isinstance(cmd, list)
        result_iter = self.ar.talk_iter(cmd)
        res = []
        for rt in result_iter:
            if rt[0] == '!trap':
                raise NasFailedResult(rt[1]['=message'])
            res.append(rt[1])
        return res

    def _exec_cmd_iter(self, cmd):
        assert isinstance(cmd, list)
        result_iter = self.ar.talk_iter(cmd)
        for rt in result_iter:
            if len(rt) < 2:
                continue
            if rt[0] == '!trap':
                raise NasFailedResult(rt[1]['=message'])
            yield rt

    # Строим объект ShapeItem из инфы, присланной из mikrotik'a
    def _build_shape_obj(self, info):
        # Переводим приставку скорости Mikrotik в Mbit/s
        def parse_speed(text_speed):
            text_speed_digit = float(text_speed[:-1] or 0.0)
            text_append = text_speed[-1:]
            if text_append == 'M':
                res = text_speed_digit
            elif text_append == 'k':
                res = text_speed_digit / 1000
            #elif text_append == 'G':
            #    res = text_speed_digit * 0x400
            else:
                res = float(re.sub(r'[a-zA-Z]', '', text_speed)) / 1000**2
            return res

        try:
            speeds = info['=max-limit'].split('/')
            t = TariffStruct(
                speedIn=parse_speed(speeds[1]),
                speedOut=parse_speed(speeds[0])
            )
            a = AbonStruct(
                uid=int(info['=name'][3:]),
                #FIXME: тут в разных микротиках или =target-addresses или =target
                ip=info['=target'][:-3],
                tariff=t
            )
            return ShapeItem(abon=a, sid=info['=.id'].replace('*', ''))
        except KeyError:
            return


class QueueManager(TransmitterManager, metaclass=ABCMeta):
    # ищем правило по имени, и возвращаем всю инфу о найденном правиле
    def find(self, name):
        ret = self._exec_cmd(['/queue/simple/print', '?name=%s' % name])
        if len(ret) > 1:
            return self._build_shape_obj(ret[0])

    def add(self, user):
        assert isinstance(user, AbonStruct)
        assert isinstance(user.tariff, TariffStruct)
        return self._exec_cmd(['/queue/simple/add',
            '=name=uid%d' % user.uid,
            #FIXME: тут в разных микротиках или =target-addresses или =target
            '=target=%s' % user.ip.get_str(),
            '=max-limit=%.3fM/%.3fM' % (user.tariff.speedOut, user.tariff.speedIn),
            '=queue=MikroBILL_SFQ/MikroBILL_SFQ',
            '=burst-time=1/1'
        ])

    def remove(self, user):
        assert isinstance(user, AbonStruct)
        q = self.find('uid%d' % user.uid)
        if q is not None:
            return self._exec_cmd(['/queue/simple/remove', '=.id=*' + str(q.sid)])

    def remove_range(self, q_ids):
        names = ['%d' % usr for usr in q_ids]
        return self._exec_cmd(['/queue/simple/remove', *names])

    def update(self, user):
        assert isinstance(user, AbonStruct)
        queue = self.find('uid%d' % user.uid)
        if queue is None:
            # не нашли запись в шейпере об абоненте, добавим
            return self.add(user)
        else:
            mk_id = queue.sid
            # обновляем шейпер абонента
            return self._exec_cmd(['/queue/simple/set', '=.id=*' + mk_id,
                '=name=uid%d' % user.uid,
                '=max-limit=%.3fM/%.3fM' % (user.tariff.speedOut, user.tariff.speedIn),
                #FIXME: тут в разных микротиках или =target-addresses или =target
                '=target=%s' % user.ip.get_str(),
                '=queue=MikroBILL_SFQ/MikroBILL_SFQ',
                '=burst-time=1/1'
            ])

    # читаем шейпер, возващаем записи о шейпере
    def read_queue_iter(self):
        queues = self._exec_cmd_iter(['/queue/simple/print', '=detail'])
        for queue in queues:
            if queue[0] == '!done': return
            yield self._build_shape_obj(queue[1])

    # то же что и выше, только получаем только номера в микротике
    def read_mikroids_iter(self):
        queues = self._exec_cmd_iter(['/queue/simple/print', '=detail'])
        for queue in queues:
            if queue[0] == '!done': return
            yield int(queue[1]['=.id'].replace('*', ''), base=16)

    def disable(self, user):
        assert isinstance(user, AbonStruct)
        q = self.find('uid%d' % user.uid)
        if q is None:
            self.add(user)
            return self.disable(user)
        else:
            return self._exec_cmd(['/queue/simple/disable', '=.id=*' + q.sid])

    def enable(self, user):
        assert isinstance(user, AbonStruct)
        q = self.find('uid%d' % user.uid)
        if q is None:
            self.add(user)
            self.enable(user)
        else:
            return self._exec_cmd(['/queue/simple/enable', '=.id=*' + q.sid])


class IpAddressListManager(TransmitterManager, metaclass=ABCMeta):

    def add(self, list_name, ip, timeout=None):
        assert isinstance(ip, IpStruct)
        commands = [
            '/ip/firewall/address-list/add',
            '=list=%s' % list_name,
            '=address=%s' % ip.get_str()
        ]
        if type(timeout) is int:
            commands.append('=timeout=%d' % timeout)
        return self._exec_cmd(commands)

    def _edit(self, ip, mk_id, timeout=None):
        assert isinstance(ip, IpStruct)
        commands = [
            '/ip/firewall/address-list/set', '=.id=' + str(mk_id),
            '?address=%s' % ip.get_str()
        ]
        if type(timeout) is int:
            commands.append('=timeout=%d' % timeout)
        return self._exec_cmd(commands)

    def remove(self, mk_id):
        return self._exec_cmd([
            '/ip/firewall/address-list/remove',
            '=.id=*' + str(mk_id)
        ])

    def find(self, ip, list_name):
        assert isinstance(ip, IpStruct)
        return self._exec_cmd([
            '/ip/firewall/address-list/print', 'where',
            '?list=%s' % list_name,
            '?address=%s' % ip.get_str()
        ])

    def disable(self, user):
        r = IpAddressListManager.find(self, user.ip, LIST_USERS_ALLOWED)
        if len(r) > 1:
            mk_id = r[0]['=.id']
            return self._exec_cmd([
                '/ip/firewall/address-list/disable',
                '=.id=' + str(mk_id),
            ])

    def enable(self, user):
        r = IpAddressListManager.find(self, user.ip, LIST_USERS_ALLOWED)
        if len(r) > 1:
            mk_id = r[0]['=.id']
            return self._exec_cmd([
                '/ip/firewall/address-list/enable',
                '=.id=' + str(mk_id),
            ])


class MikrotikTransmitter(QueueManager, IpAddressListManager):

    def add_user_range(self, user_list):
        for usr in user_list:
            self.add_user(usr)

    def remove_user_range(self, users):
        queues = [QueueManager.find(self, 'uid%d' % user.uid) for user in users if isinstance(user, AbonStruct)]
        queue_names = ["uid%d" % queue.sid for queue in queues]
        QueueManager.remove_range(self, queue_names)
        ips = [user.ip for user in users if isinstance(user, AbonStruct)]
        for ip in ips:
            ip_list_entity = IpAddressListManager.find(self, ip, LIST_USERS_ALLOWED)
            if len(ip_list_entity) > 1:
                IpAddressListManager.remove(self, ip_list_entity[0]['=.id'])

    def add_user(self, user, ip_timeout=None):
        assert isinstance(user.tariff, TariffStruct)
        assert isinstance(user.ip, IpStruct)
        QueueManager.add(self, user)
        IpAddressListManager.add(self, LIST_USERS_ALLOWED, user.ip, ip_timeout)
        # удаляем из списка заблокированных абонентов
        firewall_ip_list_obj = IpAddressListManager.find(self, user.ip, LIST_USERS_BLOCKED)
        if len(firewall_ip_list_obj) > 1:
            IpAddressListManager.remove(self, firewall_ip_list_obj[0]['=.id'])

    def remove_user(self, user):
        QueueManager.remove(self, user)
        firewall_ip_list_obj = IpAddressListManager.find(self, user.ip, LIST_USERS_ALLOWED)
        if len(firewall_ip_list_obj) > 1:
            IpAddressListManager.remove(self, firewall_ip_list_obj[0]['=.id'])

    # обновляем основную инфу абонента
    def update_user(self, user, ip_timeout=None):
        assert isinstance(user.tariff, TariffStruct)
        assert isinstance(user.ip, IpStruct)

        #ищем ip абонента в списке ip
        find_res = IpAddressListManager.find(self, user.ip, LIST_USERS_ALLOWED)

        # если не найден (mikrotik возвращает пустой словарь в списке если ничего нет)
        if len(find_res) < 2:
            # добавим запись об абоненте
            IpAddressListManager.add(self, LIST_USERS_ALLOWED, user.ip, ip_timeout)
        else:
            # если ip абонента в биллинге не такой как в mikrotik
            if find_res[0]['=address'] != user.ip.get_str():
                # то обновляем запись в mikrotik
                IpAddressListManager._edit(self, user.ip, find_res[0]['=.id'], ip_timeout)

        # Проверяем шейпер
        queue = QueueManager.find(self, 'uid%d' % user.uid)
        if queue is None:
            QueueManager.add(self, user)
            return
        if queue.abon != user:
            QueueManager.update(self, user)

    # приостановливаем обслуживание абонента
    def pause_user(self, user):
        IpAddressListManager.disable(self, user)
        QueueManager.disable(self, user)

    # продолжаем обслуживание абонента
    def start_user(self, user):
        QueueManager.enable(self, user)
        IpAddressListManager.enable(self, user)

    # Тарифы хранить нам не надо, так что методы тарифов ниже не реализуем
    def add_tariff_range(self, tariff_list):
        pass

    # соответственно и удалять тарифы не надо
    def remove_tariff_range(self, tariff_list):
        pass

    # и добавлять тоже
    def add_tariff(self, tariff):
        pass

    # и обновлять
    def update_tariff(self, tariff):
        pass

    def remove_tariff(self, tid):
        pass
