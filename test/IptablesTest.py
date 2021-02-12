from unittest import TestCase, mock
from unittest.mock import MagicMock

from util.Iptables import Iptables


class ProcessTest(TestCase):

    def test_existing(self):
        stdout = """ Chain INPUT (policy DROP)
num  target     prot opt source               destination
1    ACCEPT     all  --  0.0.0.0/0            0.0.0.0/0            ctstate RELATED,ESTABLISHED
2    ACCEPT     tcp  --  0.0.0.0/0            0.0.0.0/0            tcp dpt:222
3    ACCEPT     tcp  --  0.0.0.0/0            0.0.0.0/0            tcp dpt:80
4    ACCEPT     tcp  --  0.0.0.0/0            0.0.0.0/0            tcp dpt:443
5    ACCEPT     tcp  --  0.0.0.0/0            0.0.0.0/0            tcp dpt:8443
6    ACCEPT     all  --  0.0.0.0/0            0.0.0.0/0
7    ACCEPT     tcp  --  0.0.0.0/0            0.0.0.0/0            tcp dpt:32400
    """
        with mock.patch('util.Iptables.Process') as proc_class_mock:
            proc_mock = MagicMock()
            proc_class_mock.return_value = proc_mock
            proc_mock.get_out_lines.return_value = stdout.splitlines()
            iptables = Iptables(4)
            iptables.add_entry('tcp', 443)

            # 1 Process() instance
            calls = len(proc_class_mock.call_args_list)
            self.assertEquals(1, calls)

    def test_new(self):
        with mock.patch('util.Iptables.Process') as proc_class_mock:
            proc_mock = MagicMock()
            proc_class_mock.return_value = proc_mock
            proc_mock.get_out_lines.return_value = []
            iptables = Iptables(4)
            iptables.add_entry('tcp', 443)

            # 1 Process() instance
            calls = len(proc_class_mock.call_args_list)
            self.assertEquals(2, calls)
