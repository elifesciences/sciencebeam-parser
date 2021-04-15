FROM python:3.7.10-buster as base


# shared between builder and runtime image
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        dumb-init \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/pygrobid


# builder
FROM base as builder

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


# runtime image
FROM base

COPY --from=builder /root/.local /root/.local

COPY pygrobid ./pygrobid

COPY docker/entrypoint.sh ./docker/entrypoint.sh

COPY grobid-home ./grobid-home
COPY config.yml ./

CMD [ "--port=8070", "--host=0.0.0.0" ]
ENTRYPOINT ["/usr/bin/dumb-init", "--", "/opt/pygrobid/docker/entrypoint.sh"]
