from django.db import models, connection

from mydefs import ip2int, MyGenericIPAddressField


class IpPoolItemManager(models.Manager):
    def get_pools(self):
        ips = self.raw(r'SELECT id, ip FROM ip_pool_ippoolitem ORDER BY id')
        ips_len = len(list(ips))
        if ips_len < 1:
            return
        last_dg = ip2int(ips[0].ip)
        start_pool = last_dg
        res = list()
        cnt = 0
        for ip in ips:
            ipnt = ip2int(ip.ip)
            if ipnt > last_dg + 1 or ipnt < last_dg - 1:
                res.append((start_pool, last_dg, cnt))
                start_pool = ipnt
                cnt = 0
            last_dg = ipnt
            cnt += 1
        res.append((start_pool, last_dg, cnt))
        return res

    def add_pool(self, start_ip, end_ip):
        start_ip = ip2int(start_ip)
        end_ip = ip2int(end_ip)

        if (end_ip - start_ip) > 5000:
            raise Exception(u'Not add over 5000 ip\'s')

        sql_strs = map(lambda tip: r"(%d)" % tip, range(start_ip, end_ip + 1))
        sql = r'INSERT INTO ip_pool_ippoolitem (ip) VALUES %s' % r",".join(sql_strs)
        print sql

        cursor = connection.cursor()
        cursor.execute(sql)

    def get_free_ip(self):
        sql = r'SELECT ip_pool_ippoolitem.id as id, ip_pool_ippoolitem.ip as ip FROM ip_pool_ippoolitem ' \
              r'LEFT JOIN abonent ON abonent.ip_address_id = ip_pool_ippoolitem.id WHERE ' \
              r'abonent.ip_address_id IS NULL LIMIT 1'

        rs = self.raw(sql)
        rs_len = len(list(rs))
        return None if rs_len is 0 else rs[0]


class IpPoolItem(models.Model):
    ip = MyGenericIPAddressField()

    objects = IpPoolItemManager()

    def int_ip(self):
        return ip2int(self.ip)

    def __unicode__(self):
        return self.ip
