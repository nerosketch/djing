# -*- coding: utf-8 -*-
import socket
import binascii
from hashlib import md5
from .core import BaseTransmitter, NasFailedResult, NasNetworkError
from mydefs import ping
from .structs import TariffStruct, AbonStruct, IpStruct
from . import settings
from djing.settings import DEBUG


class ApiRos:
    "Routeros api"
    def __init__(self, sk):
        self.sk = sk
        self.currenttag = 0

    def login(self, username, pwd):
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
                    attrs[w[:j]] = w[j+1:]
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


class MikrotikTransmitter(BaseTransmitter):
    def __init__(self, login=None, password=None, ip=None, port=None):
        ip = ip or settings.NAS_IP
        if not ping(ip):
            raise NasNetworkError('NAS %s не пингуется' % ip)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, port or settings.NAS_PORT))
            self.ar = ApiRos(s)
            self.ar.login(login or settings.NAS_LOGIN, password or settings.NAS_PASSW)
        except ConnectionRefusedError:
            raise NasNetworkError('Подключение к %s отклонено (Connection Refused)' % ip)

    def _exec_cmd_iter(self, cmd):
        assert isinstance(cmd, list)
        result_iter = self.ar.talk_iter(cmd)
        for rt in result_iter:
            if rt[0] == '!trap':
                raise NasFailedResult(rt[1]['=message'])
            yield rt

    def _exec_cmd(self, cmd):
        assert isinstance(cmd, list)
        result_iter = self.ar.talk_iter(cmd)
        res = []
        for rt in result_iter:
            if rt[0] == '!trap':
                raise NasFailedResult(rt[1]['=message'])
            res.append(rt[1])
        return res

    # ищем правило по имени, и возвращаем всю инфу о найденном правиле
    def _find_queue(self, name):
        ret = self._exec_cmd(['/queue/simple/print', '?name=%s' % name])
        return ret[0]

    def add_user_range(self, user_list):
        for usr in user_list:
            self.add_user(usr)

    def remove_user_range(self, user_ids):
        names = ['%d' % usr for usr in user_ids]
        return self._exec_cmd(['/queue/simple/remove', *names])

    # добавляем правило шейпинга для указанного ip и со скоростью max-limit=Upload/Download
    # Мы уверены что user это инстанс класса agent.structs.AbonStruct
    def add_user(self, user):
        assert isinstance(user.tariff, TariffStruct)
        assert isinstance(user.ip, IpStruct)
        return self._exec_cmd(['/queue/simple/add',
            '=name=uid%d' % user.uid,
            '=target-addresses=%s/32' % user.ip.get_str(),
            '=max-limit=%fM/%fM' % (user.tariff.speedOut, user.tariff.speedIn)
        ])

    # удаляем правило шейпера по имени правила
    def remove_user(self, user):
        uid = user if type(user) is int else user.uid
        return self._exec_cmd(['/queue/simple/remove', '=name=uid%d' % uid])

    # обновляем основную инфу абонента
    def update_user(self, user):
        assert isinstance(user.tariff, TariffStruct)
        assert isinstance(user.ip, IpStruct)
        return self._exec_cmd(['/queue/simple/set', '=name=uid%d' % user.uid,
            '=max-limit=%fM/%fM' % (user.tariff.speedOut, user.tariff.speedIn),
            '=target-addresses=%s/32' % user.ip.get_str()
        ])

    # читаем абонентов, возващаем абнента и номер в микротике
    def read_users_iter(self):
        ret_it = self._exec_cmd_iter(['/queue/simple/print', '=detail'])
        for re in ret_it:
            if re[0] == '!done': return
            speeds = re[1]['=limit-at'].split('/')
            speeds = [sp.replace('M','') for sp in speeds]
            abon = AbonStruct(
                uid=int(re[1]['=name'][3:]),
                ip=IpStruct(re[1]['=target-addresses'][:-3]),
                tariff=TariffStruct(speedIn=speeds[0], speedOut=speeds[1])
            )
            yield abon

    # то же что и выше, только получаем номера в микротике
    def read_users_mikroids_iter(self):
        ret_it = self._exec_cmd_iter(['/queue/simple/print', '=detail'])
        for re in ret_it:
            if re[0] == '!done': return
            yield int(re[1]['=.id'].replace('*', ''), base=16)

    # приостановливаем обслуживание абонента
    # в @user передаём номер в микротике
    def pause_user(self, user):
        self._exec_cmd(['/queue/simple/disable', user])

    # продолжаем обслуживание абонента
    # в @user передаём номер в микротике
    def start_user(self, user):
        self._exec_cmd(['/queue/simple/enable', user])

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
