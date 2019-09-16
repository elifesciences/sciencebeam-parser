import logging
from contextlib import contextmanager
from typing import Iterable

import requests
from urllib3.util.retry import Retry


LOGGER = logging.getLogger(__name__)


METHOD_WHITELIST_WITH_POST = frozenset(
    Retry.DEFAULT_METHOD_WHITELIST | {'POST'}
)

DEFAULT_STATUS_FORCELIST = (500, 502, 503, 504,)


def configure_session_retry(
        session=None,
        max_retries=3,
        max_redirect=5,
        backoff_factor=1,
        status_forcelist: Iterable[int] = DEFAULT_STATUS_FORCELIST,
        method_whitelist: Iterable[str] = None,
        **kwargs):

    retry = Retry(
        connect=max_retries,
        read=max_retries,
        status_forcelist=status_forcelist,
        method_whitelist=method_whitelist,
        redirect=max_redirect,
        backoff_factor=backoff_factor
    )
    LOGGER.debug('retry: %s', retry)
    session.mount('http://', requests.adapters.HTTPAdapter(max_retries=retry, **kwargs))
    session.mount('https://', requests.adapters.HTTPAdapter(max_retries=retry, **kwargs))


@contextmanager
def RetrySession(**kwargs):
    with requests.Session() as session:
        configure_session_retry(session=session, **kwargs)
        yield session
