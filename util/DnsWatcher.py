import socket
from abc import abstractmethod
from time import sleep
from typing import List, Optional, Callable, Dict

from util.Loggable import Loggable


class EntryListener:
    @abstractmethod
    def dns_entry_changed(self):
        pass


class EntryWatch(Loggable):
    def __init__(self, address: str, stack: int):
        super().__init__('EntryWatch')
        self._address: str = address
        self._stack: int = socket.AF_INET6 if stack == 6 else socket.AF_INET
        self.listener: List[Callable] = []

        self._last_ip: Optional[str] = None

    def check(self):
        """
        Checks if the dns entry has been changed
        """
        ips = self.resolve_ips()

        last_ip = None
        for ip in ips:
            if self._last_ip is None:
                self._last_ip = ip
                return
            if self._last_ip == ip:
                return

            last_ip = ip

        self._last_ip = last_ip
        # IP has changed, notify listeners
        for listener in self.listener:
            listener(last_ip)

    def add_listener(self, callback_method: Callable):
        self.listener.append(callback_method)

    def resolve(self) -> str:
        ips = self.resolve_ips()
        return ips[0]

    def resolve_ips(self) -> List[str]:
        try:
            reply = socket.getaddrinfo(self._address, None, self._stack)
        except socket.gaierror:
            self.log.error('Could not resolve ' + self._address + ' for stack ' + str(self._stack))
            raise

        ips = []
        for entry in reply:
            af, socktype, proto, canonname, sa = entry
            ips.append(sa[0])
        return ips


class DnsWatcher:
    """
    Watches for DNS changes
    """

    _check: bool = False
    """
    Indicates if the dns watch is running
    """

    _addrs: Dict[str, EntryWatch] = {}

    def add(self, addr: str, stack: int, callback_method: Callable) -> EntryWatch:
        """
        Adds a new domain which should be monitored
        :param addr: Domain
        :param stack: IP stack (4 or 6)
        :param callback_method: Method which should be called on change
        """
        key = str(stack) + addr
        if key in self._addrs:
            watch = self._addrs[key]
            watch.add_listener(callback_method)
            return watch

        watch = EntryWatch(addr, stack)
        watch.add_listener(callback_method)
        self._addrs[key] = watch
        return watch

    def check(self):
        """
        Checks for changed dns entries
        """
        for watchers in self._addrs.values():
            watchers.check()

    def stop(self):
        self._check = False

    def wait_for_changes(self):
        """
        Checks for DNS changes in regular intervals.
        This call blocks until "stop" is called
        """
        self._check = True
        while self._check:
            self.check()
            sleep(60)
