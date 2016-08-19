# -*- coding:utf-8 -*-


class FirewallManager(object):

    f = r'/sbin/ipfw -q'

    # вызывает комманду shell
    def exec_cmd(self, cmd):
        print cmd
        #os.execv(cmd, [''])

    # ставит заглушку на абонента
    def set_cap(self, user):
        pass

    # Открывает доступ в интернет
    def open_inet_door(self, user):
        if not user.tariff:
            print u'WARNING: User does not have a tariff'
            return
        cmd = r"%s table 12 add %s/32 %d && %s table 13 add %s/32 %d" % (
            self.f, user.ip_str(), user.tariff.tid,
            self.f, user.ip_str(), user.tariff.tid+1000
        )
        self.exec_cmd(cmd)

    # Закрывает доступ в интернет
    def close_inet_door(self, user):
        cmd = r"%s table 12 del %s/32 && %s table 13 del %s/32" % (
            self.f, user.ip_str(),
            self.f, user.ip_str()
        )
        self.exec_cmd(cmd)

    # Создаёт тариф (пайпы, режущие скорость
    def make_tariff(self, tariff):
        cmd = r"make ipfw tariff :)"
        self.exec_cmd(cmd)

    # Убирает тариф из фаервола
    def destroy_tariff(self, tariff):
        cmd = r"destroy ipfw tariff :)"
        self.exec_cmd(cmd)

    def reset(self):
        cmd = r"%s -f flush && %s table all flush" % (self.f, self.f)
        self.exec_cmd(cmd)
