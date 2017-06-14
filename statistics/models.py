import math
from datetime import datetime, timedelta, date, time
from django.db import models, connection
from django.utils.timezone import now

from mydefs import MyGenericIPAddressField
from .fields import UnixDateTimeField


class StatManager(models.Manager):

    def chart(self, ip_addr, count_of_parts=12, want_date=date.today()):
        def byte_to_mbit(x):
            return ((x/60)*8)/2**20

        def split_list(lst, chunk_count):
            chunk_size = len(lst) // chunk_count
            if chunk_size == 0:
                chunk_size = 1
            return [lst[i:i+chunk_size] for i in range(0, len(lst), chunk_size)]

        def avarage(elements):
            return sum(elements) / len(elements)

        charts_data = self.filter(ip=ip_addr)
        charts_times = [cd.cur_time.timestamp()*1000 for cd in charts_data]
        charts_octets = [cd.octets for cd in charts_data]
        if len(charts_octets) > 0 and len(charts_octets) == len(charts_times):
            charts_octets = split_list(charts_octets, count_of_parts)
            charts_octets = [byte_to_mbit(avarage(c)) for c in charts_octets]

            charts_times = split_list(charts_times, count_of_parts)
            charts_times = [avarage(t) for t in charts_times]

            charts_data = zip(charts_times, charts_octets)
            charts_data = ["{x: new Date(%d), y: %.2f}" % (cd[0], cd[1]) for cd in charts_data]
            midnight = datetime.combine(want_date, time.min)
            charts_data.append("{x:new Date(%d),y:0}" % (int(charts_times[-1:][0]) + 1))
            charts_data.append("{x:new Date(%d),y:0}" % (int((midnight + timedelta(days=1)).timestamp()) * 1000))
            return charts_data
        else:
            return

    def get_dates(self):
        tables = connection.introspection.table_names()
        tables = [t.replace('flowstat_', '') for t in tables if t.startswith('flowstat_')]
        return [datetime.strptime(t, '%d%m%Y').date() for t in tables]


class StatElem(models.Model):
    cur_time = UnixDateTimeField(primary_key=True)
    ip = MyGenericIPAddressField()
    octets = models.PositiveIntegerField(default=0)
    packets = models.PositiveIntegerField(default=0)

    objects = StatManager()

    def save(self, *args, **kwargs):
        return

    def delete(self, *args, **kwargs):
        return

    @staticmethod
    def percentile(N, percent, key=lambda x:x):
        """
        Find the percentile of a list of values.

        @parameter N - is a list of values. Note N MUST BE already sorted.
        @parameter percent - a float value from 0.0 to 1.0.
        @parameter key - optional key function to compute value from each element of N.

        @return - the percentile of the values
        """
        if not N:
            return None
        k = (len(N)-1) * percent
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return key(N[int(k)])
        d0 = key(N[int(f)]) * (c-k)
        d1 = key(N[int(c)]) * (k-f)
        return d0+d1

    class Meta:
        abstract = True


def getModel(want_date=now()):

    class DynamicStatElem(StatElem):
        class Meta:
            db_table = 'flowstat_%s' % want_date.strftime("%d%m%Y")
            abstract = False
    return DynamicStatElem


class StatCache(models.Model):
    last_time = UnixDateTimeField()
    ip = MyGenericIPAddressField(primary_key=True)
    octets = models.PositiveIntegerField(default=0)
    packets = models.PositiveIntegerField(default=0)

    def is_online(self):
        return self.last_time > now() - timedelta(minutes=55)

    def is_today(self):
        return date.today() == self.last_time.date()


    class Meta:
        db_table = 'flowcache'
