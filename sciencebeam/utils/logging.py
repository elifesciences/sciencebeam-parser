import logging


def configure_logging(
        level=logging.WARNING,
        sciencebeam_level=logging.INFO):
    logging.basicConfig(level=level)
    logging.getLogger('sciencebeam').setLevel(sciencebeam_level)
    logging.getLogger('sciencebeam_utils').setLevel(sciencebeam_level)
