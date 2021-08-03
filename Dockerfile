FROM python:3.7.10-buster AS base


# shared between builder and runtime image
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        dumb-init \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/sciencebeam_parser


# builder
FROM base AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.build.txt ./
RUN pip install --disable-pip-version-check --no-warn-script-location --user -r requirements.build.txt

COPY requirements.cpu.txt ./
RUN pip install --disable-pip-version-check --no-warn-script-location --user -r requirements.cpu.txt

COPY requirements.delft.txt ./
RUN pip install --disable-pip-version-check --no-warn-script-location --user -r requirements.delft.txt --no-deps

COPY requirements.txt ./
RUN pip install --disable-pip-version-check --no-warn-script-location --user -r requirements.txt


# dev image
FROM builder AS dev

COPY requirements.dev.txt ./
RUN pip install --disable-pip-version-check --no-warn-script-location --user -r requirements.dev.txt

COPY sciencebeam_parser ./sciencebeam_parser
COPY tests ./tests
COPY test-data ./test-data
COPY .flake8 .pylintrc setup.py config.yml ./


# runtime image
FROM base AS runtime

COPY --from=builder /root/.local /root/.local

COPY sciencebeam_parser ./sciencebeam_parser

COPY docker/entrypoint.sh ./docker/entrypoint.sh

COPY config.yml ./

ENV SCIENCEBEAM_DELFT_MAX_SEQUENCE_LENGTH=2000
ENV SCIENCEBEAM_DELFT_INPUT_WINDOW_STRIDE=1800

CMD [ "--port=8070", "--host=0.0.0.0" ]
ENTRYPOINT ["/usr/bin/dumb-init", "--", "/opt/sciencebeam_parser/docker/entrypoint.sh"]
