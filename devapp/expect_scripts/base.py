import re
import sys
from pexpect import spawn


class ZteOltConsoleError(Exception):
    pass


class OnuZteRegisterError(ZteOltConsoleError):
    pass


class ZTEFiberIsFull(ZteOltConsoleError):
    pass


class ZteOltLoginFailed(ZteOltConsoleError):
    pass


class ExpectValidationError(ValueError):
    pass


class MySpawn(spawn):
    def __init__(self, *args, **kwargs):
        super(MySpawn, self).__init__(encoding='utf-8', *args, **kwargs)
        self.logfile = sys.stdout

    def do_cmd(self, c, prompt):
        self.sendline(c)
        return self.expect_exact(prompt)

    def get_lines(self):
        return self.buffer.split('\r\n')

    def get_lines_before(self):
        return self.before.split('\r\n')


def parse_onu_name(onu_name: str, name_regexp=re.compile('[/:_]')):
    gpon_onu, stack_num, rack_num, fiber_num, onu_num = name_regexp.split(onu_name)
    return {
        'stack_num': stack_num,
        'rack_num': rack_num,
        'fiber_num': fiber_num,
        'onu_num': onu_num
    }


def get_unregistered_onu(lines, serial):
    for line in lines:
        if line.startswith('gpon-onu_'):
            spls = re.split(r'\s+', line)
            if len(spls) > 2:
                if serial == spls[1]:
                    onu_index, sn, state = spls[:3]
                    return parse_onu_name(onu_index)


def get_free_registered_onu_number(lines):
    onu_type_regexp = re.compile(r'^\s{1,5}onu \d{1,3} type [-\w\d]{4,64} sn \w{4,64}$')
    onu_olt_num = None
    i = 0
    for l in lines:
        if onu_type_regexp.match(l):
            # match line
            i += 1
            onu, num, onu_type, onu_type, sn, onu_sn = l.split()
            onu_olt_num = int(num)
            if onu_olt_num > i:
                return i
    if onu_olt_num is None:
        return 1
    return onu_olt_num + 1


def sn_to_mac(sn: str):
    if not sn: return
    t = sn[4:].lower()
    r = tuple(t[i:i + 2] for i in range(0, len(t), 2))
    return '45:47:%s' % ':'.join(r)


def onu_conv(rack_num: int, fiber_num: int, port_num: int):
    r = "10000{0:08b}{1:08b}00000000".format(rack_num, fiber_num)
    snmp_fiber_num = int(r, base=2)
    return "%d.%d" % (snmp_fiber_num, port_num)
