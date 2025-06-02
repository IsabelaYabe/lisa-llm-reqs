import logging
from logging import FileHandler, StreamHandler, Formatter
from lisa.sub_lisa.decorators import singleton

@singleton
class CustomLogger:
    """
        CustomLogger Class

        This class provides a flexible and configurable logging solution using Python's built-in logging module.
        It allows the creation of a logger instance with customized file and console handlers, each configured 
        with specific formatting and logging levels.

        The CustomLogger class supports:
        - Configurable log level and log file name.
        - Separate console and file handlers to manage logging outputs.

        Attributes:
            log_file (str): The path to the file where log messages are saved.
            level (int): The default logging level for console output.
            logger (Logger): The main logger instance created for logging messages.
            handlers (list): A list of logging handlers, such as file and console handlers.

        Methods:
            _create_file_handler: Sets up the file handler with specific formatting and logging level.
            _create_console_handler: Sets up the console handler with specific formatting and logging level.
            add_handler: Adds an external logging handler to the logger.
            _setup_logger: Initializes the logger with all specified handlers.
            get_logger: Returns the logger instance for use in other modules.

        Helper Function:
            setup_logger(): Returns an instance of CustomLogger's logger for convenient access to a pre-configured logger.
    """
    def __init__(self, log_file="app.log", level=logging.DEBUG, handlers=None):
        """
        Initializes the CustomLogger instance with specified file path, log level, handlers.

        Args:
            log_file (str): The path to the file where log messages are saved. Default is "app.log".
            level (int): The default logging level for console output. Default is logging.DEBUG.
            handlers (list, optional): Custom handlers for the logger. If None, default file and console handlers are used.
        """
        self.log_file = log_file
        self.level = level
        self.logger = logging.getLogger(__name__)
        self.handlers = handlers or [self._create_file_handler(), self._create_console_handler()]
        self._setup_logger()

    def _create_file_handler(self):
        """
        Creates a file handler for logging with a specific formatter and level. 

        The file handler is configured to append to the existing log file if it exists, ensuring that previous logs
        are preserved.

        Returns:
            FileHandler: A configured file handler for logging to a file.
        """
        file_log_formatter = Formatter("%(asctime)s | %(levelname)s | %(module)s:%(funcName)s - %(message)s")
        file_handler = FileHandler(self.log_file, mode="a", encoding="utf-8")

        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(file_log_formatter)

        return file_handler
    
    def _create_console_handler(self):
        """
        Creates and configures a console handler for logging with specific formatting and level.

        Returns:
            StreamHandler: A configured console handler for displaying logs in the console.
        """
        console_log_formatter = Formatter(
            "%(asctime)s | %(levelname)s | %(module)s:%(funcName)s:line%(lineno)d - %(message)s")
        console_handler = StreamHandler()
        
        console_handler.setLevel(self.level)
        console_handler.setFormatter(console_log_formatter)
        
        return console_handler
    
    def add_handler(self, handler):
        """
        Adds an external logging handler to the logger.

        Args:
            handler (logging.Handler): The handler to be added to the logger.
        """
        self.logger.addHandler(handler)

    def _setup_logger(self):
        """
        Sets up the logger by adding all specified handlers and setting the logging level.
        """
        for handler in self.handlers:
            self.add_handler(handler)
        self.logger.setLevel(self.level)

    def get_logger(self):
        """
        Returns the logger instance for use in other modules.

        Returns:
            Logger: The main logger instance configured with file and console handlers.
        """
        return self.logger
    
logger = CustomLogger().get_logger()

if __name__ == "__main__":
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")