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
def redirect_logging_to_tqdm(logger: logging.Logger = None):
    if logger is None:
        logger = logging.root
    tqdm_handler = TqdmLoggingHandler()
    console_handlers = [
        handler
        for handler in logger.handlers
        if isinstance(handler, logging.StreamHandler) and handler.stream in {sys.stdout, sys.stderr}
    ]
    if console_handlers:
        tqdm_handler.setFormatter(console_handlers[0].formatter)
    try:
        logger.addHandler(tqdm_handler)
        for handler in console_handlers:
            logger.removeHandler(handler)
        yield
    finally:
        logger.removeHandler(tqdm_handler)
        for handler in console_handlers:
            logger.addHandler(handler)


@contextmanager
def tqdm_with_logging_redirect(*args, logger: logging.Logger = None, **kwargs):
    with tqdm(*args, **kwargs) as pbar:
        with redirect_logging_to_tqdm(logger=logger):
            yield pbar
