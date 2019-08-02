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
        except:  # noqa pylint: disable=bare-except
            self.handleError(record)


def _is_console_logging_handler(handler: logging.Handler) -> bool:
    return isinstance(handler, logging.StreamHandler) and handler.stream in {sys.stdout, sys.stderr}


@contextmanager
def redirect_logging_to_tqdm(logger: logging.Logger = None):
    if logger is None:
        logger = logging.root
    tqdm_handler = TqdmLoggingHandler()
    original_handlers = logger.handlers
    try:
        logger.handlers = [
            handler
            for handler in logger.handlers
            if not _is_console_logging_handler(handler)
        ] + [tqdm_handler]
        yield
    finally:
        logger.handlers = original_handlers


@contextmanager
def tqdm_with_logging_redirect(*args, logger: logging.Logger = None, **kwargs):
    with tqdm(*args, **kwargs) as pbar:
        with redirect_logging_to_tqdm(logger=logger):
            yield pbar
