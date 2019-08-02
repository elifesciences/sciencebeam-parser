import logging
import sys
from contextlib import contextmanager

from tqdm import tqdm


class TqdmLoggingHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.write(msg)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:  # pylint: disable=bare-except
            self.handleError(record)


@contextmanager
def redirect_log_to_tqdm():
    tqdm_handler = TqdmLoggingHandler()
    console_handlers = [
        handler
        for handler in logging.root.handlers
        if isinstance(handler, logging.StreamHandler) and handler.stream in {sys.stdout, sys.stderr}
    ]
    if console_handlers:
        tqdm_handler.setFormatter(console_handlers[0].formatter)
    try:
        logging.root.addHandler(tqdm_handler)
        for handler in console_handlers:
            logging.root.removeHandler(handler)
        yield
    finally:
        logging.root.removeHandler(tqdm_handler)
        for handler in console_handlers:
            logging.root.addHandler(handler)
