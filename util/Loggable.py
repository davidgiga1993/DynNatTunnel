import builtins
import logging
import sys
from threading import Lock


class LogConfigProvider:
    """
    Provides the configuration for the logging facilities
    """

    def __init__(self, write_log: bool):
        self.__write_log = write_log
        self._console_log_level = logging.DEBUG

    def set_console_log_level(self, log_level):
        """
        Gets the log level for the stdout logging
        :param log_level: Log level (logging.DEBUG, logging.WARN,...)
        """
        self._console_log_level = log_level

    def get_handlers(self):
        """
        Returns a list with all loggers that should be added to the logging facility
        """
        handlers = []
        ch = logging.StreamHandler(self.get_log_stream())
        ch.setLevel(self.get_console_log_level())
        ch.setFormatter(logging.Formatter(self._get_log_format_console()))
        handlers.append(ch)

        return handlers

    def get_log_stream(self):
        """
        Returns the stream which should be used for the console logging.

        :return: sys.stdout
        """
        return sys.stdout

    def get_console_log_level(self) -> int:
        """
        Returns the log level for the stdout logging
        """
        return self._console_log_level

    def _get_log_format_console(self) -> str:
        """
        Returns the format string for the console
        """
        return '%(levelname)-.1s %(asctime)-.19s [%(name)s] %(message)s'


class Loggable:
    __lock = Lock()
    """
    Lock for synchronizing logger creation
    """

    def __init__(self, name: str):
        """
        Creates a new logger instance

        :param name: name of the logger
        """
        super().__init__()

        # only define log if it is not already defined
        # this test is required because of the multiple inheritance from python
        if not hasattr(self, 'log'):
            self.log = Loggable.create_logger(name)
            """
            Logger
            :type log: logger
            """

    def update_logger(self):
        """
        Updates the logger instance for this object.
        This might be required if the file logging was enabled
        """
        self.log = Loggable.create_logger(self.log.name)

    @staticmethod
    def shutdown():
        """
        Shuts down all logger.
        """
        logging.shutdown()

    @staticmethod
    def set_config_provider(config_provider: LogConfigProvider):
        """
        Sets the config provider that should be used to create loggers
        :param: Config provider
        """
        builtins.LOG_CONFIG_FACILITY = config_provider

    @staticmethod
    def create_logger(name: str):
        config_provider = Loggable.get_config_provider()

        Loggable.__lock.acquire()
        try:
            logger = logging.getLogger(name)
            logger.handlers = []
            logger.setLevel(logging.DEBUG)
            for handler in config_provider.get_handlers():
                logger.addHandler(handler)
        finally:
            Loggable.__lock.release()

        return logger

    @staticmethod
    def get_config_provider():
        """
        Returns the current configuration provider
        :return: configuration provider
        :rtype: LogConfigProvider
        """
        if 'LOG_CONFIG_FACILITY' in __builtins__:
            config_provider = __builtins__['LOG_CONFIG_FACILITY']
        else:
            # no custom config provider set - create new
            config_provider = LogConfigProvider(False)
            Loggable.set_config_provider(config_provider)
        return config_provider
