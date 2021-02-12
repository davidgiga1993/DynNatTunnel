import os
import subprocess
import threading
from typing import List, Optional, Dict

from util.Events import EventHook
from util.Loggable import Loggable


class AsyncStreamReader(Loggable):
    """
    Reads a given byte stream in a new thread and notifies about new incoming data.
    The data will be read as utf-8 encoded string.
    """

    def __init__(self):
        """
        Creates a new stream reader instance
        """
        super().__init__('AsyncStreamReader')
        self.on_new_data = EventHook()
        """
        New data received event
        """
        self.__stream = None
        """
        Stream which should be read
        """
        self.__thread: Optional[threading.Thread] = None
        """
        Thread for reading the stream
        """

    def set_stream(self, stream):
        """
        Sets the stream which should be read.
        This must be called before "start()"
        :param stream:  stream which should be read
        """
        self.__stream = stream

    def start(self):
        """
        Starts the read thread.
        """

        def read_stream():
            self.log.debug('Read thread started')
            while True:
                line = self.__stream.readline()
                if not line:
                    break

                line = self.decode_message(line)
                self.on_new_data.fire(line)

            self.log.debug('Read thread stopped')

        self.__thread = threading.Thread(target=read_stream, name='stream-thread')
        self.__thread.start()

    def join(self):
        """
        Joins the read thread
        """
        self.__thread.join()

    @staticmethod
    def decode_message(message: bytes) -> str:
        """
        Decodes a byte array as a UTF-8 string
        :param message: message
        :return: UTF-8 decoded string
        """

        return message.decode('utf-8', 'backslashreplace')

    @staticmethod
    def encode_message(message: str) -> bytes:
        """
        Encodes a string as UTF-8 bytes
        :param message: Message as string
        :return: Bytes
        """
        return message.encode('utf-8')


class Process(Loggable):
    def __init__(self, process_args: List[str]):
        """
        Creates a new process object

        :param process_args: array with process name and args
        """
        super().__init__('Process')

        self.out: str = ''
        """ Raw output of the process"""

        self.err: str = ''
        """ Raw std err output of the process"""

        self.__working_directory: str = os.getcwd()
        """ Working directory that should be used for the process"""

        self.__process_args: List[str] = process_args
        """
        Process name and arguments for executing
        """

        self.__timeout: int = 0
        """
        Timeout for the process to complete its execution in seconds.
        If the value is "0" the timeout will be disabled
        """

        self.__process: Optional[subprocess.Popen] = None
        """
        The process object
        """

        self.__ignore_errors: bool = False
        """ Indicates if the return value of the process should throw an exception or not"""

        self.__collect_output: bool = False
        """ When True, the output will be redirected to a local variable"""

        self.__env: Dict[str, str] = os.environ.copy()
        """ Environment variables for the process"""

        self.__stdin: Optional[str] = None
        """ Commands that should be send to the stdin of the process after it was started"""

        self.__use_shell: bool = False
        """ Controls if the process should be executed in a shell environment """

        self._print_output: bool = True
        """ Controls if the process output should be printed to the console
        """

        self.__stdout_reader = AsyncStreamReader()
        """
        Reader for the stdout
        """
        self.__stderr_reader = AsyncStreamReader()
        """
        Reader for the stderr
        """

    def hide_output(self):
        """
        Disables printing the stdout/err of the process
        """
        self._print_output = False

    def ignore_errors(self):
        """
        Disables the validation of the return value of the process execution.
        """
        self.__ignore_errors = True

    def get_std_out_reader(self) -> AsyncStreamReader:
        """
        Returns the STD out reader.
        :return: reader object
        """
        return self.__stdout_reader

    def stdin(self, stdin: str, keep_open=False):
        """
        Sets the stdin that should be send to the process after it was started.
        If the process is already running, the stdin will be directly send.
        :param stdin: stdin for the process
        :param keep_open: True if the stream should be kept open afterwards
        """

        self.__stdin = stdin

        if self.__process is not None and self.__stdin is not None:
            # Process is running -> directly send
            encoded = AsyncStreamReader.encode_message(self.__stdin)
            self.__process.stdin.write(encoded)
            self.__process.stdin.flush()
            if not keep_open:
                self.__process.stdin.close()
            return

    def collect_output(self):
        """
        Enables stdout collecting. This will redirect the stdout of the process to a local stream.
        The result is available in "out".
        """
        self.__collect_output = True

    def get_out_lines(self) -> List[str]:
        """
        Returns the process output, split by lines
        :return: lines
        """
        return self.out.splitlines()

    def get_std_err_lines(self) -> List[str]:
        """
        Returns the process std err output, split by lines
        :return: lines
        """
        return self.err.splitlines()

    def stop(self):
        """
        Stops the process
        """
        if self.__process is None:
            return

        self.__process.terminate()

    def run(self) -> int:
        """
        Executes the process in the current thread.
        :return int process result
        :raises ProcessException: Gets raised when the result of the process was not 0
        and "ignore_errors" was not called
        """

        self.log.info('Starting ' + self.__process_args[0])
        pipe_stdio = self.__collect_output or self._print_output or self.__stdin is not None

        args = {'args': self.__process_args, 'env': self.__env, 'cwd': self.__working_directory,
                'shell': self.__use_shell}

        if pipe_stdio:
            args['stdout'] = subprocess.PIPE
            args['stderr'] = subprocess.PIPE
            args['stdin'] = subprocess.PIPE

        self.__process = subprocess.Popen(**args)

        # Set the stdin again so it will be send to the process
        self.stdin(self.__stdin)

        if pipe_stdio:
            # Only start stdio threads if the output should be collected or shown
            self.__start_stdio_threads()

        # Wait for the process to complete
        self.__process.wait()
        result = self.__process.poll()
        self.log.debug('Process completed with code ' + str(result))

        # Remove object so other threads know the process terminated
        self.__process = None

        if pipe_stdio:
            # Only join stdio threads if they were started in the first place
            self.__stderr_reader.join()
            self.__stdout_reader.join()

        if not self.__ignore_errors and result != 0:
            if self.__collect_output:
                raise subprocess.SubprocessError(
                    'Process returned ' + str(result) + '\n' + str(self.out) + "\n" + str(self.err))

            raise subprocess.SubprocessError('Process returned ' + str(result))
        return result

    def set_timeout(self, timeout: int):
        """
        Sets the maximum execution time the process can run before being
        gracefully stopped

        :param timeout: timeout in seconds
        """
        self.__timeout = timeout

    def set_environment(self, param: Dict[str, str]):
        """
        Sets the environment variables that should be used when executing the process.
        New environment variables will be added to the existing ones.
        Existing ones will be overwritten by this call.

        :param param: dict with environment variables
        """
        self.__env.update(param)

    def set_working_directory(self, path: str):
        """
        Sets the working directory that should be used for the process.
        By default this will be the current working directory.
        """
        self.__working_directory = path

    def print_debug(self):
        """
        Prints the arguments of the process and the current environment variables
        """
        self.log.debug(str(self.__process_args))
        self.log.debug(self.__env)

    def print_args(self):
        """
        Prints the process arguments as info loglevel
        """
        self.log.info(str(self.__process_args))

    def __start_stdio_threads(self):
        """
        Starts two threads which read the stdout and stderr of the process.
        """

        def new_stdout_data(line):
            if self._print_output:
                self.log.info(line.strip())
            if self.__collect_output:
                self.out += line

        def new_stderr_data(line):
            if self._print_output:
                self.log.error(line.strip())
            if self.__collect_output:
                self.err += line

        self.__stdout_reader.set_stream(self.__process.stdout)
        self.__stderr_reader.set_stream(self.__process.stderr)
        self.__stdout_reader.on_new_data += new_stdout_data
        self.__stderr_reader.on_new_data += new_stderr_data

        self.__stdout_reader.start()
        self.__stderr_reader.start()
