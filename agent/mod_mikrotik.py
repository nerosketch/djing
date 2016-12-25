# -*- coding: utf-8 -*-
import socket
import binascii
from hashlib import md5
from core import BaseTransmitter, NasFailedResult
from structs import TariffStruct, IpStruct


class ApiRos:
    "Routeros api"

    def __init__(self, sk):
        self.sk = sk
        self.currenttag = 0

    def login(self, username, pwd):
        for repl, attrs in self.talk(["/login"]):
            chal = binascii.unhexlify(attrs['=ret'])
        md = md5()
        md.update('\x00')
        md.update(pwd)
        md.update(chal)
        self.talk(["/login", "=name=" + username,
                   "=response=00" + binascii.hexlify(md.digest())])

    def talk(self, words):
        if self.writeSentence(words) == 0: return
        r = []
        while 1:
            i = self.readSentence()
            if len(i) == 0: continue
            reply = i[0]
            attrs = {}
            for w in i[1:]:
                j = w.find('=', 1)
                if j == -1:
                    attrs[w] = ''
                else:
                    attrs[w[:j]] = w[j + 1:]
            r.append((reply, attrs))
            if reply == '!done': return r

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
        print "<<< " + w
        self.writeLen(len(w))
        self.writeStr(w)

    def readWord(self):
        ret = self.readStr(self.readLen())
        print ">>> " + ret
        return ret

    def writeLen(self, l):
        if l < 0x80:
            self.writeStr(chr(l))
        elif l < 0x4000:
            l |= 0x8000
            self.writeStr(chr((l >> 8) & 0xFF))
            self.writeStr(chr(l & 0xFF))
        elif l < 0x200000:
            l |= 0xC00000
            self.writeStr(chr((l >> 16) & 0xFF))
            self.writeStr(chr((l >> 8) & 0xFF))
            self.writeStr(chr(l & 0xFF))
        elif l < 0x10000000:
            l |= 0xE0000000
            self.writeStr(chr((l >> 24) & 0xFF))
            self.writeStr(chr((l >> 16) & 0xFF))
            self.writeStr(chr((l >> 8) & 0xFF))
            self.writeStr(chr(l & 0xFF))
        else:
            self.writeStr(chr(0xF0))
            self.writeStr(chr((l >> 24) & 0xFF))
            self.writeStr(chr((l >> 16) & 0xFF))
            self.writeStr(chr((l >> 8) & 0xFF))
            self.writeStr(chr(l & 0xFF))

    def readLen(self):
        c = ord(self.readStr(1))
        if (c & 0x80) == 0x00:
            pass
        elif (c & 0xC0) == 0x80:
            c &= ~0xC0
            c <<= 8
            c += ord(self.readStr(1))
        elif (c & 0xE0) == 0xC0:
            c &= ~0xE0
            c <<= 8
            c += ord(self.readStr(1))
            c <<= 8
            c += ord(self.readStr(1))
        elif (c & 0xF0) == 0xE0:
            c &= ~0xF0
            c <<= 8
            c += ord(self.readStr(1))
            c <<= 8
            c += ord(self.readStr(1))
            c <<= 8
            c += ord(self.readStr(1))
        elif (c & 0xF8) == 0xF0:
            c = ord(self.readStr(1))
            c <<= 8
            c += ord(self.readStr(1))
            c <<= 8
            c += ord(self.readStr(1))
            c <<= 8
            c += ord(self.readStr(1))
        return c

    def writeStr(self, text):
        n = 0
        while n < len(text):
            r = self.sk.send(text[n:])
            if r == 0: raise RuntimeError, "connection closed by remote end"
            n += r

    def readStr(self, length):
        ret = ''
        while len(ret) < length:
            s = self.sk.recv(length - len(ret))
            if s == '': raise RuntimeError, "connection closed by remote end"
            ret += s
        return ret


class MikrotikTransmitter(BaseTransmitter):
    def __init__(self, login, password, ip, port=8728):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
        self.ar = ApiRos(s)
        self.ar.login(login, password)

    def _exec_cmd(self, cmd):
        assert isinstance(cmd, list)
        result = self.ar.talk(cmd)
        for rt in result:
            if rt[0] == '!trap':
                raise NasFailedResult, rt[1]['=message']
        return result

    # ищем правило по имени, и возвращаем всю инфу о найденном правиле
    def _find_queue(self, name):
        ret = self._exec_cmd(['/queue/simple/print', '?name=%s' % name])
        return ret[0][1]

    def add_user_range(self, user_list):
        return map(self.add_user, user_list)

    def remove_user_range(self, user_list):
        names = ['uid%d' % usr.uid for usr in user_list]
        return self._exec_cmd(['/queue/simple/remove', '=.id=%s' % ','.join(names)])

    # добавляем правило шейпинга для указанного ip и со скоростью max-limit=Upload/Download
    # Мы уверены что user это инстанс класса agent.structs.AbonStruct
    def add_user(self, user):
        assert isinstance(user.tariff, TariffStruct)
        assert isinstance(user.ip, IpStruct)
        return self._exec_cmd(['/queue/simple/add',
            '=name=uid%d' % user.uid,
            '=target=%s/32' % user.ip.get_str(),
            '=max-limit=%fM/%fM' % (user.tariff.speedOut, user.tariff.speedIn)
        ])

    # удаляем правило шейпера по имени правила
    def remove_user(self, user):
        uid = user if type(user) is int else user.uid
        self._exec_cmd(['/queue/simple/remove', '=.id=uid%d' % uid])

    # обновляем основную инфу абонента
    def update_user(self, user):
        assert isinstance(user.tariff, TariffStruct)
        assert isinstance(user.ip, IpStruct)
        self._exec_cmd(['/queue/simple/set', '=.id=uid%d' % user.uid,
            '=max-limit=%fM/%fM' % (user.tariff.speedOut, user.tariff.speedIn),
            '=target=%s/32' % user.ip.get_str()
        ])

    # Тарифы хранить нам не надо, так что методы тарифов ниже не реализуем
    def add_tariff_range(self, tariff_list):
        pass

    # todo: реальзовать
    def remove_tariff_range(self, tariff_list):
        pass

    # todo: реальзовать
    def add_tariff(self, tariff):
        pass

    # todo: реальзовать
    def update_tariff(self, tariff):
        pass

    # todo: реальзовать
    def remove_tariff(self, tid):
        pass
