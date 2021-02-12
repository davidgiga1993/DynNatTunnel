from typing import Optional

from config.Config import ForwardConfig
from util.DnsWatcher import DnsWatcher, EntryWatch
from util.Iptables import Iptables
from util.Socat import SocatBuilder, Socat


class Tunnel:
    """
    Represents a single tunnel
    """

    def __init__(self, config: ForwardConfig, dest_addr: str, dns_watcher: DnsWatcher):
        self._config = config
        self._dest_addr: str = dest_addr
        self._socat: Optional[Socat] = None

        self._dns_entry: EntryWatch = dns_watcher.add(dest_addr, config.dest.stack, self._dns_changed)
        self._iptables = Iptables(config.src.stack)

    def start(self):
        """
        Starts the tunnel
        """
        self._iptables.add_entry(self._config.prot, self._config.src.port)

        ip_addr = self._dns_entry.resolve()
        self._start_tunnel(ip_addr)

    def stop(self):
        self._stop_tunnel()
        self._iptables.remove_entry(self._config.prot, self._config.src.port)

    def _start_tunnel(self, dest_ip: str):
        self._socat = SocatBuilder().protocol(self._config.prot) \
            .from_address(self._config.src.port, self._config.src.stack) \
            .to_address(dest_ip, self._config.dest.port, self._config.dest.stack) \
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
