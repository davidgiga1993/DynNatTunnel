import argparse
import json
import logging
import os
import signal
import sys

from config.Config import Config
from util.DnsWatcher import DnsWatcher
from util.Loggable import Loggable
from util.Tunnel import Tunnel


def main():
    config = Loggable.get_config_provider()
    config.set_console_log_level(logging.INFO)
    Loggable.set_config_provider(config)

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', dest='config', default='config.json', help='Config which should be used')
    args = parser.parse_args()
    if not os.path.isfile(args.config):
        raise FileNotFoundError('Config not found: ' + str(args.config))

    with open(args.config) as file:
        config = Config(json.load(file))

    dns_watcher = DnsWatcher()
    tunnels = []
    for forwarder in config.forwarders:
        tunnels.append(Tunnel(forwarder, config.dest_addr, dns_watcher))

    for tunnel in tunnels:
        tunnel.start()

    def signal_handler(sig, frame):
        # Gracefully terminate to revert the iptables config
        dns_watcher.stop()
        for t in tunnels:
            t.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    dns_watcher.wait_for_changes()


if __name__ == '__main__':
    main()
