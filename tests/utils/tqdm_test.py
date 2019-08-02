from __future__ import absolute_import

import logging
import sys
from io import StringIO

from sciencebeam.utils.tqdm import (
    redirect_logging_to_tqdm,
    tqdm_with_logging_redirect,
    TqdmLoggingHandler
)


LOGGER = logging.getLogger(__name__)


class TestRedirectLoggingToTqdm:
    def test_should_add_and_remove_tqdm_handler(self):
        logger = logging.Logger('test')
        with redirect_logging_to_tqdm(logger=logger):
            assert len(logger.handlers) == 1
            assert isinstance(logger.handlers[0], TqdmLoggingHandler)
        assert not logger.handlers

    def test_should_remove_and_restore_console_handlers(self):
        logger = logging.Logger('test')
        stderr_console_handler = logging.StreamHandler(sys.stderr)
        stdout_console_handler = logging.StreamHandler(sys.stderr)
        logger.handlers = [stderr_console_handler, stdout_console_handler]
        with redirect_logging_to_tqdm(logger=logger):
            assert len(logger.handlers) == 1
            assert isinstance(logger.handlers[0], TqdmLoggingHandler)
        assert logger.handlers == [stderr_console_handler, stdout_console_handler]

    def test_should_inherit_console_logger_formatter(self):
        logger = logging.Logger('test')
        formatter = logging.Formatter('custom: %(message)')
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(formatter)
        logger.handlers = [console_handler]
        with redirect_logging_to_tqdm(logger=logger):
            assert logger.handlers[0].formatter == formatter

    def test_should_not_remove_stream_handlers_not_fot_stdout_or_stderr(self):
        logger = logging.Logger('test')
        stream_handler = logging.StreamHandler(StringIO())
        logger.addHandler(stream_handler)
        with redirect_logging_to_tqdm(logger=logger):
            assert len(logger.handlers) == 2
            assert logger.handlers[0] == stream_handler
            assert isinstance(logger.handlers[1], TqdmLoggingHandler)
        assert logger.handlers == [stream_handler]


class TestTqdmWithLoggingRedirect:
    def test_should_add_and_remove_handler_from_root_logger_by_default(self):
        original_handlers = list(logging.root.handlers)
        with tqdm_with_logging_redirect(total=1) as pbar:
            assert isinstance(logging.root.handlers[-1], TqdmLoggingHandler)
            LOGGER.info('test')
            pbar.update(1)
        assert logging.root.handlers == original_handlers

    def test_should_add_and_remove_handler_from_custom_logger(self):
        logger = logging.Logger('test')
        with tqdm_with_logging_redirect(total=1, logger=logger) as pbar:
            assert len(logger.handlers) == 1
            assert isinstance(logger.handlers[0], TqdmLoggingHandler)
            LOGGER.info('test')
            pbar.update(1)
