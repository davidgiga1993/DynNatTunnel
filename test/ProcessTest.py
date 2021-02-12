import os
import threading
from time import sleep
from unittest import TestCase

from util.Process import Process


class ProcessTest(TestCase):

    def test_wait(self):
        if os.name == 'nt':
            proc = Process(['cmd', '/c', 'pause'])
        else:
            proc = Process(['bash', '-c', 'sleep 100'])

        threading.Thread(target=proc.run).start()
        sleep(1)
        proc.stop()
