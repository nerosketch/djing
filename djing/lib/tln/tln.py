#!/usr/bin/env python3
import re
import struct
from telnetlib import Telnet
from time import sleep
from typing import Generator, Dict, Optional, Tuple


class ZteOltConsoleError(Exception):
    pass


class OnuZteRegisterError(ZteOltConsoleError):
    pass


class ZTEFiberIsFull(ZteOltConsoleError):
    pass


class ZTEFiberNumberNotFound(ZteOltConsoleError):
    pass


class ValidationError(ValueError):
    pass


MAC_ADDR_REGEX = b'^([0-9A-Fa-f]{1,2}[:-]){5}([0-9A-Fa-f]{1,2})$'
IP_ADDR_REGEX = '^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.' \
                '(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.' \
                '(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.' \
                '(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
ONU_SN_REGEX = b'^ZTEG[A-F\d]{8}$'


class TelnetApi(Telnet):
    config_level = []

    def __init__(self, *args, **kwargs):
        timeout = kwargs.get('timeout')
        if timeout:
            self._timeout = timeout
        self._prompt_string = b'ZTE-C320-PKP#'
        super().__init__(*args, **kwargs)

    def write(self, buffer: bytes) -> None:
        buffer = buffer + b'\n'
        print('>>', buffer)
        super().write(buffer)

    def resize_screen(self, width: int, height: int):
        naws_cmd = struct.pack('>BBBHHBB',
                               255, 250, 31,     # IAC SB NAWS
                               width, height,
                               255, 240          # IAC SE
                               )
        sock = self.get_socket()
        sock.send(naws_cmd)

    def enter(self, username: bytes, passw: bytes) -> None:
        self.read_until(b'Username:')
        self.write(username)
        self.read_until(b'Password:')
        self.write(passw)

    def read_lines(self) -> Generator:
        while True:
            line = self.read_until(b'\r\n', timeout=self._timeout)
            line = line.replace(b'\r\n', b'')
            if self._prompt_string == line:
                break
            if line == b'':
                continue
            yield line

    def command_to(self, cmd: bytes) -> Generator:
        self.write(cmd)
        return self.read_lines()

    def set_prompt_string(self, prompt_string: bytes) -> None:
        self.config_level.append(prompt_string)
        self._prompt_string = prompt_string

    def level_exit(self) -> Optional[Tuple]:
        if len(self.config_level) < 2:
            print('We are in root')
            return
        self.config_level.pop()
        self.set_prompt_string(self.config_level[-1])
        return tuple(self.command_to(b'exit'))

    def __del__(self):
        if self.sock:
            self.write(b'exit')
        super().__del__()


def parse_onu_name(onu_name: bytes, name_regexp=re.compile(b'[/:_]')) -> Dict[str, bytes]:
    gpon_onu, stack_num, rack_num, fiber_num, onu_num = name_regexp.split(onu_name)
    return {
        'stack_num': stack_num,
        'rack_num': rack_num,
        'fiber_num': fiber_num,
        'onu_num': onu_num
    }


class OltZTERegister(TelnetApi):

    def __init__(self, screen_size: Tuple[int, int], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resize_screen(*screen_size)

    def get_unregistered_onu(self, sn: bytes) -> Optional[Dict]:
        lines = tuple(self.command_to(b'show gpon onu uncfg'))
        if len(lines) > 3:
            # devices available
            # find onu by sn
            line = tuple(ln for ln in lines if sn.lower() in ln.lower())
            if len(line) > 0:
                line = line[0]
                onu_name, onu_sn, onu_state = line.split()
                onu_numbers = parse_onu_name(onu_name)
                onu_numbers.update({
                    'onu_name': onu_name,
                    'onu_sn': onu_sn,
                    'onu_state': onu_state
                })
                return onu_numbers

    def get_last_registered_onu_number(self, stack_num: int, rack_num: int, fiber_num: int) -> int:
        registered_lines = self.command_to(b'show run int gpon-olt_%d/%d/%d' % (
            stack_num,
            rack_num,
            fiber_num
        ))
        onu_type_regexp = re.compile(b'^\s{2}onu \d{1,3} type [-\w\d]{4,64} sn \w{4,64}$')
        last_onu = 0
        for rl in registered_lines:
            if rl == b' --More--':
                self.write(b' ')
            if onu_type_regexp.match(rl):
                _onu, num, _type, onu_type, _sn, onu_sn = rl.split()
                last_onu = int(num)
        return last_onu

    def enter_to_config_mode(self) -> bool:
        prompt = b'ZTE-C320-PKP(config)#'
        self.set_prompt_string(prompt)
        res = tuple(self.command_to(b'config terminal'))
        if res[1].startswith(b'Enter configuration commands'):
            # ok, we in the config mode
            return True
        return False

    def go_to_olt_interface(self, stack_num: int, rack_num: int, fiber_num: int) -> Tuple:
        self.set_prompt_string(b'ZTE-C320-PKP(config-if)#')
        return tuple(self.command_to(b'interface gpon-olt_%d/%d/%d' % (
            stack_num,
            rack_num,
            fiber_num
        )))

    def go_to_onu_interface(self, stack_num: int, rack_num: int, fiber_num: int, onu_port_num: int) -> Tuple:
        self.set_prompt_string(b'ZTE-C320-PKP(config-if)#')
        return tuple(self.command_to(b'interface gpon-onu_%d/%d/%d:%d' % (
            stack_num,
            rack_num,
            fiber_num,
            onu_port_num
        )))

    def apply_conf_to_onu(self, mac_addr: bytes, vlan_id: int) -> None:
        tmpl = (
            b'switchport vlan %d tag vport 1' % vlan_id,
            b'port-location format flexible-syntax vport 1',
            b'port-location sub-option remote-id enable vport 1',
            b'port-location sub-option remote-id name %s vport 1' % mac_addr,
            b'dhcp-option82 enable vport 1',
            b'dhcp-option82 trust true replace vport 1',
            b'ip dhcp snooping enable vport 1'
        )
        for conf_line in tmpl:
            self.write(conf_line)

    def register_onu_on_olt_fiber(self, onu_type: bytes, new_onu_num: int, onu_sn: bytes, line_profile: bytes,
                                  remote_profile: bytes) -> Tuple:
        # ok, we in interface
        tpl = b'onu %d type %s sn %s' % (new_onu_num, onu_type, onu_sn)
        r = tuple(self.command_to(tpl))
        return tuple(self.command_to(b'onu %d profile line %s remote %s' % (
            new_onu_num,
            line_profile,
            remote_profile
        ))) + r


def register_onu_ZTE_F660(olt_ip: str, onu_sn: bytes, login_passwd: Tuple[bytes, bytes], onu_mac: bytes):
    onu_type = b'ZTE-F660'
    line_profile = b'ZTE-F660-LINE'
    remote_profile = b'ZTE-F660-ROUTER'
    if not re.match(MAC_ADDR_REGEX, onu_mac):
        raise ValidationError
    if not re.match(IP_ADDR_REGEX, olt_ip):
        raise ValidationError
    if not re.match(ONU_SN_REGEX, onu_sn):
        raise ValidationError

    tn = OltZTERegister(host=olt_ip, timeout=2, screen_size=(120, 128))
    tn.enter(*login_passwd)

    unregistered_onu = tn.get_unregistered_onu(onu_sn)
    if unregistered_onu is None:
        raise OnuZteRegisterError('unregistered onu not found, sn=%s' % onu_sn.decode('utf-8'))

    stack_num = int(unregistered_onu['stack_num'])
    rack_num = int(unregistered_onu['rack_num'])
    fiber_num = int(unregistered_onu['fiber_num'])

    last_onu_number = tn.get_last_registered_onu_number(
        stack_num, rack_num, fiber_num
    )

    if last_onu_number < 1:
        raise ZTEFiberNumberNotFound
    elif last_onu_number > 126:
        raise ZTEFiberIsFull('olt fiber %d is full' % fiber_num)

    # enter to config
    if not tn.enter_to_config_mode():
        raise ZteOltConsoleError('Failed to enter to config mode')

    # go to olt interface
    if not tn.go_to_olt_interface(stack_num, rack_num, fiber_num):
        raise ZteOltConsoleError('Failed to enter in olt fiber port')

    # new onu port number
    new_onu_port_num = last_onu_number + 1

    # register onu on olt interface
    r = tn.register_onu_on_olt_fiber(onu_type, new_onu_port_num, onu_sn, line_profile, remote_profile)
    print(r)

    # exit from olt interface
    tn.level_exit()

    r = tn.go_to_onu_interface(stack_num, rack_num, fiber_num, new_onu_port_num)
    print(r)

    tn.apply_conf_to_onu(onu_mac, 145)
    sleep(1)
    return


if __name__ == '__main__':
    ip = '10.40.1.10'
    try:
        register_onu_ZTE_F660(
            olt_ip=ip, onu_sn=b'ZTEGC0458DCE', login_passwd=(b'admin', b'2ekc3'),
            onu_mac=b'cc:7b:35:8b:7:0'
        )
    except ZteOltConsoleError as e:
        print(e)
    except ConnectionRefusedError:
        print('ERROR: connection refused', ip)
