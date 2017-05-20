import math
from datetime import datetime, timedelta
from django.db import models, ProgrammingError
from django.utils import timezone
from mydefs import MyGenericIPAddressField
from .fields import UnixDateTimeField
from mydefs import LogicError


class StatManager(models.Manager):

    def traffic_by_ip(self, ip):
        try:
            traf = self.order_by('-cur_time').filter(ip=ip, octets__gt=524288)[0]
            now = datetime.now()
            if traf.cur_time < now - timedelta(minutes=55):
                return False, traf
            else:
                return True, traf
        except IndexError:
            return False, None
        except ProgrammingError as e:
            raise LogicError(e)


class StatElem(models.Model):
    cur_time = UnixDateTimeField(primary_key=True)
    ip = MyGenericIPAddressField()
    octets = models.PositiveIntegerField(default=0)
    packets = models.PositiveIntegerField(default=0)

    objects = StatManager()

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


def getModel():

    class DynamicStatElem(StatElem):
        class Meta:
            db_table = 'flowstat_%s' % timezone.now().strftime("%d%m%Y")
            abstract = False
    return DynamicStatElem
