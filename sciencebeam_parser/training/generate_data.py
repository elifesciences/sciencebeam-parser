import logging
from typing import List, Optional


LOGGER = logging.getLogger(__name__)


def main(argv: Optional[List[str]] = None):
    LOGGER.info('argv: %r', argv)


if __name__ == '__main__':
    logging.basicConfig(level='INFO')

    main()
