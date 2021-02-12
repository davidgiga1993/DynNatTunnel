import re
import subprocess
from typing import List, Optional

from util.Loggable import Loggable
from util.Process import Process


class Rule:
    def __init__(self, num: int, target: str, protocol: str, port: int):
        self.num = num
        self.target = target
        self.protocol = protocol
        self.port = port


class Iptables(Loggable):
    """

    """

    def __init__(self, stack: int):
        super().__init__('Iptables')
        self._stack = stack

    def get_entry(self, prot: str, port: int) -> Optional[Rule]:
        args = ['-L', 'input', '-n', '--line-number']
        out = self._execute(args)
        rules = self._parse_table(out)
        for rule in rules:
            if rule.target != 'ACCEPT':
                continue
            if rule.port != port:
                continue
            if rule.protocol != 'all' and rule.protocol != prot:
                continue

            return rule
        return None

    def add_entry(self, prot: str, port: int):
        try:
            rule = self.get_entry(prot, port)
            if rule is not None:
                # Matching rule found -> Do nothing
                return

            args = ['-A', 'INPUT', '-p', prot, '--dport', str(port), '-j', 'ACCEPT']

            self._execute(args)
        except subprocess.SubprocessError:
            self.log.warning('Could not add iptables rule for ' + prot + ':' + str(port))

    def remove_entry(self, prot: str, port: int):
        try:
            rule = self.get_entry(prot, port)
            if rule is None:
                # No matching rule found -> Do nothing
                return
            args = ['-D', 'INPUT', str(rule.num)]
            self._execute(args)
        except subprocess.SubprocessError:
            self.log.warning('Could not remove iptables rule for ' + prot + ':' + str(port))

    def _execute(self, args: List[str]) -> List[str]:
        bin_name = 'ip6tables' if self._stack == 6 else 'iptables'
        args.insert(0, bin_name)

        proc = Process(args)
        proc.collect_output()
        proc.hide_output()
        proc.run()
        return proc.get_out_lines()

    def _parse_table(self, lines: List[str]) -> List[Rule]:
        rules = []
        for line in lines:
            columns = re.split(" +", line)
            num = columns[0]
            if not num.isdigit():
                continue
            num = int(num)
            target = columns[1]
            prot = columns[2]
            last_col = columns[-1]
            if 'dpt' not in last_col:
                continue

            parts = last_col.split(':', 2)
            port = int(parts[1])
            rules.append(Rule(num, target, prot, port))
        return rules
