FROM python:3.7.10-buster AS base


# shared between builder and runtime image
RUN apt-get update \
    && apt-get install --assume-yes --no-install-recommends \
        dumb-init \
        poppler-utils \
        libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/sciencebeam_parser

ENV VENV=/opt/venv
ENV VIRTUAL_ENV=${VENV} PYTHONUSERBASE=${VENV} PATH=${VENV}/bin:$PATH


# builder-base
FROM base AS builder-base

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libtesseract4 \
        tesseract-ocr-eng \
        libtesseract-dev \
        libleptonica-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.build.txt ./
RUN python3 -m venv ${VENV} \
    && pip install --disable-pip-version-check --no-warn-script-location -r requirements.build.txt


FROM builder-base AS builder

COPY requirements.cpu.txt ./
RUN pip install --disable-pip-version-check --no-warn-script-location \
    -r requirements.cpu.txt

COPY requirements.txt ./
RUN pip install --disable-pip-version-check --no-warn-script-location \
    -r requirements.txt

COPY requirements.delft.txt ./
RUN pip install --disable-pip-version-check --no-warn-script-location \
    -r requirements.delft.txt --no-deps


# builder
FROM builder-base AS builder-cv

COPY requirements.cpu.txt ./
RUN pip install --disable-pip-version-check --no-warn-script-location \
    -r requirements.cpu.txt

COPY requirements.cv.txt ./
RUN pip install --disable-pip-version-check --no-warn-script-location \
    -r requirements.cv.txt

COPY requirements.ocr.txt ./
RUN pip install --disable-pip-version-check --no-warn-script-location \
    -r requirements.ocr.txt

COPY requirements.txt ./
RUN pip install --disable-pip-version-check --no-warn-script-location \
    -r requirements.txt

COPY requirements.delft.txt ./
RUN pip install --disable-pip-version-check --no-warn-script-location \
    -r requirements.delft.txt --no-deps


# dev image
FROM builder-cv AS dev

COPY requirements.dev.txt ./
RUN pip install --disable-pip-version-check --no-warn-script-location \
    -r requirements.dev.txt

COPY sciencebeam_parser ./sciencebeam_parser
COPY tests ./tests
COPY test-data ./test-data
COPY .flake8 .pylintrc setup.py config.yml ./

# temporary workaround for tesserocr https://github.com/sirfz/tesserocr/issues/165
ENV LC_ALL=C


# runtime image
FROM base AS runtime

COPY --from=builder /opt/venv /opt/venv

COPY sciencebeam_parser ./sciencebeam_parser

COPY docker/entrypoint.sh ./docker/entrypoint.sh

COPY config.yml ./

ENV SCIENCEBEAM_DELFT_MAX_SEQUENCE_LENGTH=2000
ENV SCIENCEBEAM_DELFT_INPUT_WINDOW_STRIDE=1800

CMD [ "--port=8070", "--host=0.0.0.0" ]
ENTRYPOINT ["/usr/bin/dumb-init", "--", "/opt/sciencebeam_parser/docker/entrypoint.sh"]


# runtime-cv image
FROM base AS runtime-cv

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libtesseract4 \
        tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder-cv /opt/venv /opt/venv

COPY sciencebeam_parser ./sciencebeam_parser

COPY docker/entrypoint.sh ./docker/entrypoint.sh

COPY config.yml ./

ENV SCIENCEBEAM_DELFT_MAX_SEQUENCE_LENGTH=2000
ENV SCIENCEBEAM_DELFT_INPUT_WINDOW_STRIDE=1800

# temporary workaround for tesserocr https://github.com/sirfz/tesserocr/issues/165
ENV LC_ALL=C

CMD [ "--port=8070", "--host=0.0.0.0" ]
ENTRYPOINT ["/usr/bin/dumb-init", "--", "/opt/sciencebeam_parser/docker/entrypoint.sh"]
