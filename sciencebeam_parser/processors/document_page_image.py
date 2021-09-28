import logging
from time import monotonic
from typing import Iterable, NamedTuple, Optional, Sequence

import pdf2image


LOGGER = logging.getLogger(__name__)


DEFAULT_PDF_RENDER_DPI = 200


class DocumentPageImage(NamedTuple):
    page_number: int
    page_image_path: str


def iter_pdf_document_page_images(
    pdf_path: str,
    output_dir: str,
    thread_count: int = 1,
    dpi: float = DEFAULT_PDF_RENDER_DPI,
    page_numbers: Optional[Sequence[int]] = None
) -> Iterable[DocumentPageImage]:
    first_page: int = 1
    last_page: Optional[int] = None
    if page_numbers:
        first_page = min(page_numbers)
        last_page = max(page_numbers)
    render_start = monotonic()
    output_files = pdf2image.convert_from_path(
        pdf_path=pdf_path,
        first_page=first_page,
        last_page=last_page,
        dpi=dpi,
        paths_only=True,
        output_folder=output_dir,
        thread_count=thread_count
    )
    render_end = monotonic()
    LOGGER.info(
        'rendered PDF pages, took=%.3fs, page_count=%d, dpi=%s, thread_count=%d',
        render_end - render_start,
        len(output_files),
        dpi,
        thread_count
    )
    for page_index, output_file in enumerate(output_files):
        page_number = first_page + page_index
        if page_numbers is not None and page_number not in page_numbers:
            LOGGER.debug('ignoring deselected page: %d (%s)', page_number, page_numbers)
            continue
        yield DocumentPageImage(
            page_number=page_number,
            page_image_path=output_file
        )
