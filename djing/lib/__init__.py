import socket
import struct
from datetime import timedelta
from collections import Iterator
from django.db import models


def ip2int(addr):
    try:
        return struct.unpack("!I", socket.inet_aton(addr))[0]
    except:
        return 0


def int2ip(addr):
    try:
        return socket.inet_ntoa(struct.pack("!I", addr))
    except:
        return ''


def safe_float(fl):
    try:
        return 0.0 if fl is None or fl == '' else float(fl)
    except ValueError:
        return 0.0


def safe_int(i):
    try:
        return 0 if i is None or i == '' else int(i)
    except ValueError:
        return 0


class MyGenericIPAddressField(models.GenericIPAddressField):
    description = "Int32 notation ip address"

    def __init__(self, protocol='ipv4', *args, **kwargs):
        super(MyGenericIPAddressField, self).__init__(protocol=protocol, *args, **kwargs)
        self.max_length = 8

    def get_prep_value(self, value):
        # strIp to Int
        value = super(MyGenericIPAddressField, self).get_prep_value(value)
        return ip2int(value)

    def to_python(self, value):
        return value

    def get_internal_type(self):
        return 'PositiveIntegerField'

    @staticmethod
    def from_db_value(value, expression, connection, context):
        return int2ip(value) if value != 0 else None

    def int_ip(self):
        return ip2int(self)


# Предназначен для Django CHOICES чтоб можно было передавать классы вместо просто описания поля,
# классы передавать для того чтоб по значению кода из базы понять какой класс нужно взять для нужной функциональности.
# Например по коду в базе вам нужно определять как считать тариф абонента, что реализовано в возвращаемом классе.
class MyChoicesAdapter(Iterator):
    chs = tuple()
    current_index = 0
    _max_index = 0

    # На вход принимает кортеж кортежей, вложенный из 2х элементов: кода и класса, как: TARIFF_CHOICES
    def __init__(self, choices):
        self._max_index = len(choices)
        self.chs = choices

    def __next__(self):
        if self.current_index >= self._max_index:
            raise StopIteration
        else:
            e = self.chs
            ci = self.current_index
            res = e[ci][0], e[ci][1].description()
            self.current_index += 1
            return res


# Russian localized timedelta
class RuTimedelta(timedelta):
    def __new__(cls, tm):
        if isinstance(tm, timedelta):
            return timedelta.__new__(
                cls,
                days=tm.days,
                seconds=tm.seconds,
                microseconds=tm.microseconds
            )

    def __str__(self):
        # hours, remainder = divmod(self.seconds, 3600)
        # minutes, seconds = divmod(remainder, 60)
        # text_date = "%d:%d" % (
        #    hours,
        #    minutes
        # )
        if self.days > 1:
            ru_days = 'дней'
            if 5 > self.days > 1:
                ru_days = 'дня'
            elif self.days == 1:
                ru_days = 'день'
            # text_date = '%d %s %s' % (self.days, ru_days, text_date)
            text_date = '%d %s' % (self.days, ru_days)
        else:
            text_date = ''
        return text_date


class MultipleException(Exception):
    def __init__(self, err_list):
        if not isinstance(err_list, (list, tuple)):
            raise TypeError
        self.err_list = err_list


class LogicError(Exception):
    pass


def singleton(class_):
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return getinstance
