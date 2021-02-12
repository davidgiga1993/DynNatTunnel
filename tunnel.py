import argparse
import json
import logging
import os
import signal
import sys

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
        config = json.load(file)

    dest_addr = config['dest']
    dns_watcher = DnsWatcher()
    tunnels = []
    for item in config['forward']:
        tunnels.append(Tunnel(item, dest_addr, dns_watcher))

    for tunnel in tunnels:
        tunnel.start()

    def signal_handler(sig, frame):
        for tunnel in tunnels:
            tunnel.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


if __name__ == '__main__':
    main()
