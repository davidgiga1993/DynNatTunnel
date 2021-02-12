from unittest import TestCase, mock

from util.DnsWatcher import DnsWatcher


class EntryWatchTest(TestCase):
    def test_change(self):
        self._callbacks = 0

        def callback():
            self._callbacks += 1

        with mock.patch('util.DnsWatcher.socket') as socket_mock:
            socket_mock.getaddrinfo.return_value = [(0, 0, 0, '1.1.1.1', 0)]

            watcher = DnsWatcher()
            watcher.add('google.com', 4, callback)
            watcher.check()
            self.assertEquals(0, self._callbacks)

            socket_mock.getaddrinfo.return_value = [(0, 0, 0, '1.1.1.1', 0)]
            watcher.check()
            self.assertEquals(0, self._callbacks)

            socket_mock.getaddrinfo.return_value = [(0, 0, 0, '1.1.1.2', 0)]
            watcher.check()
            self.assertEquals(1, self._callbacks)

            watcher.check()
            self.assertEquals(1, self._callbacks)
