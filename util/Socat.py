from __future__ import annotations

import threading
from typing import Optional

from util.Process import Process


class Socat:
    """
    Wrapper for the socat binary
    """

    PROT_TCP = 0
    PROT_UDP = 1

    STACK_IPV_4 = 4
    STACK_IPV_6 = 6

    def __init__(self, prot: int, src_stack: int, src_port: int, dst_stack: int, dst_port: int, dst_address: str):
        self._prot: int = prot
        self._src_stack: int = src_stack
        self._src_port: int = src_port
        self._dst_stack: int = dst_stack
        self._dst_port: int = dst_port
        self._dst_address: str = dst_address

        self._proc: Optional[Process] = None

    def start(self):
        args = ['socat']

        if self._prot == Socat.PROT_TCP:
            prot_str = 'TCP'
        else:
            prot_str = 'UDP'

        src = prot_str
        src += str(self._src_stack) + '-LISTEN'
        src += ':' + str(self._src_port) + ',fork,su=nobody'
        args.append(src)

        dst = prot_str
        dst += str(self._dst_stack) + ':'
        if self._dst_stack == 6:
            dst += '['
        dst += self._dst_address
        if self._dst_stack == 6:
            dst += ']'

        dst += ':' + str(self._dst_port)
        args.append(dst)

        self._proc = Process(args)
        self._proc.print_args()
        threading.Thread(target=self._start_socat).start()

    def stop(self):
        if self._proc is None:
            return

        self._proc.stop()
        self._proc = None

    def _start_socat(self):
        self._proc.run()


class SocatBuilder:
    def __init__(self):
        self._prot = Socat.PROT_TCP

        self._src_stack = Socat.STACK_IPV_4
        self._src_port = None
        self._dst_stack = Socat.STACK_IPV_6
        self._dst_port = None
        self._dst_address = None

    def protocol(self, protocol: str) -> SocatBuilder:
        protocol = protocol.lower()
        if protocol != 'tcp' and protocol != 'udp':
            raise ValueError('Unknown protocol: ' + protocol)

        self._prot = Socat.PROT_TCP if protocol == 'tcp' else Socat.PROT_UDP
        return self

    def from_address(self, port: int, stack: int = Socat.STACK_IPV_4) -> SocatBuilder:
        self._validate_port('src', port)
        self._src_port = port
        self._validate_stack('src', stack)
        self._src_stack = stack
        return self

    def to_address(self, ip_addr: str, port: int, stack: int = Socat.STACK_IPV_4) -> SocatBuilder:
        self._validate_port('dst', port)
        self._dst_port = port
        self._validate_stack('dst', stack)
        self._dst_stack = stack
        self._dst_address = ip_addr
        return self

    def build(self) -> Socat:
        return Socat(self._prot, self._src_stack, self._src_port,
                     self._dst_stack, self._dst_port, self._dst_address)

    @staticmethod
    def _validate_stack(tag: str, stack: int):
        if stack == Socat.STACK_IPV_6 or stack == Socat.STACK_IPV_4:
            return
        raise ValueError('Invalid ' + tag + ' stack: ' + str(stack))

    @staticmethod
    def _validate_port(tag: str, port: int):
        if 0 < port < 65535:
            return
        raise ValueError('Invalid ' + tag + ' port: ' + str(port))
