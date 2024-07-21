import logging
from logging.handlers import RotatingFileHandler
import sys
import queue


class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(self.format(record))


def setup_logger(name='qa_dataset_generator', log_file=None, level=logging.DEBUG, gui_queue=None):
    logger = logging.getLogger()  # Root logger
    logger.setLevel(level)

    # Remove any existing handlers to avoid duplicate logs
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler (if log_file is provided)
    if log_file:
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # GUI Queue Handler (if gui_queue is provided)
    if gui_queue:
        queue_handler = QueueHandler(gui_queue)
        queue_handler.setFormatter(formatter)
        logger.addHandler(queue_handler)

    # Set logging level for other modules
    logging.getLogger('openai').setLevel(level)
    logging.getLogger('requests').setLevel(level)
    logging.getLogger('urllib3').setLevel(level)

    return logger


def get_logger(name='qa_dataset_generator'):
    """
    Get a logger by name. If the logger doesn't exist, it will be created with default settings.

    :param name: Name of the logger
    :return: Logger instance
    """
    return logging.getLogger(name)


class LogManager:
    """
    A class to manage logging across the application.
    It ensures that the logging is set up only once and provides methods to access loggers.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LogManager, cls).__new__(cls)
            cls._instance.setup_done = False
        return cls._instance

    def setup_logging(self, log_file='qa_generator.log', level=logging.INFO, gui_queue=None):
        """
        Set up logging for the entire application.
        This should be called once at the start of the application.
        """
        if not self.setup_done:
            self.root_logger = setup_logger(
                log_file=log_file, level=level, gui_queue=gui_queue)
            self.setup_done = True

    def get_logger(self, name='qa_dataset_generator'):
        """
        Get a logger by name.
        """
        if not self.setup_done:
            raise RuntimeError(
                "Logging has not been set up. Call setup_logging first.")
        return logging.getLogger(name)


# Example usage
if __name__ == "__main__":
    # Set up logging
    log_manager = LogManager()
    log_manager.setup_logging(level=logging.DEBUG)

    # Get a logger and use it
    logger = log_manager.get_logger(__name__)
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

    # Test GUI queue
    gui_queue = queue.Queue()
    log_manager.setup_logging(gui_queue=gui_queue)
    logger.info("This message should go to the GUI queue")
    print("Message in GUI queue:", gui_queue.get())
