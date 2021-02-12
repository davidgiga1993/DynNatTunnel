from typing import Optional

from util.DnsWatcher import DnsWatcher, EntryWatch
from util.Iptables import Iptables
from util.Socat import SocatBuilder, Socat


class Tunnel:
    """
    Represents a single tunnel
    """

    def __init__(self, config: dict, dest_addr: str, dns_watcher: DnsWatcher):
        self._protocol: str = config['prot']
        self._src: dict = config['src']
        self._dest: dict = config['dst']
        self._dest_addr: str = dest_addr
        self._socat: Optional[Socat] = None

        self._dns_entry: EntryWatch = dns_watcher.add(dest_addr, self._dest['stack'], self._dns_changed)
        self._iptables = Iptables(self._src['stack'])

    def start(self):
        """
        Starts the tunnel
        """
        self._iptables.add_entry(self._protocol, self._src['port'])

        ip_addr = self._dns_entry.resolve()
        self._start_tunnel(ip_addr)

    def stop(self):
        self._stop_tunnel()
        self._iptables.remove_entry(self._protocol, self._src['port'])

    def _start_tunnel(self, dest_ip: str):
        self._socat = SocatBuilder().protocol(self._protocol) \
            .from_address(self._src['port'], self._src['stack']) \
            .to_address(dest_ip, self._dest['port'], self._dest['stack']) \
            .build()

        self._socat.start()

    def _stop_tunnel(self):
        if self._socat is None:
            return

        self._socat.stop()
        self._socat = None

    def _dns_changed(self, new_addr: str):
        # DNS of destination has been changed -> Restart tunnel
        self._stop_tunnel()
        self._start_tunnel(new_addr)
