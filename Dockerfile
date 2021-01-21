FROM python:3.7.9-buster

# install LibreOffice Write to convert Word to PDF
# also install fonts and fontconfig to provide common fonts or configuration to their alternatives
RUN apt-get update \
  && apt-get install -y \
    libreoffice-writer \
    fonts-liberation fonts-liberation2 \
    fonts-crosextra-carlito fonts-crosextra-caladea \
    fontconfig \
  && rm -rf /var/lib/apt/lists/*

ENV PROJECT_HOME=/srv/sciencebeam

ENV VENV=${PROJECT_HOME}/venv
RUN python3 -m venv ${VENV}
ENV PYTHONUSERBASE=${VENV} PATH=${VENV}/bin:$PATH

WORKDIR ${PROJECT_HOME}

COPY requirements.pip.txt ${PROJECT_HOME}/
RUN pip install -r requirements.pip.txt

COPY requirements.build.txt ${PROJECT_HOME}/
RUN pip install -r requirements.build.txt

COPY requirements.prereq.txt ${PROJECT_HOME}/
RUN pip install -r requirements.prereq.txt

COPY requirements.txt ${PROJECT_HOME}/
RUN pip install -r requirements.txt

ARG install_dev
COPY requirements.dev.txt ./
RUN if [ "${install_dev}" = "y" ]; then pip install -r requirements.dev.txt; fi

COPY sciencebeam ${PROJECT_HOME}/sciencebeam
COPY xslt ${PROJECT_HOME}/xslt
COPY *.cfg *.conf *.sh *.in *.txt *.py ${PROJECT_HOME}/

RUN pip install -e . --no-deps

ARG commit
ARG version
COPY docker ./docker
RUN ./docker/set-version.sh "${version}" "${commit}"

RUN useradd -ms /bin/bash sciencebeam
USER sciencebeam
ENV HOME=/home/sciencebeam

# set and check UNO_PATH, UNO_PYTHON_PATH and UNO_OFFICE_BINARY_PATH
ENV UNO_PATH=/usr/lib/python3/dist-packages
ENV UNO_PYTHON_PATH=python3.7
ENV UNO_OFFICE_BINARY_PATH=/usr/lib/libreoffice/program/soffice.bin
RUN \
  echo "UNO_PATH: ${UNO_PATH}" \
  && ls -l ${UNO_PATH} \
  && echo "UNO_PYTHON_PATH: ${UNO_PYTHON_PATH}" \
  && PYTHONPATH=${UNO_PATH} ${UNO_PYTHON_PATH} -c 'import uno, unohelper' \
  && echo "UNO_OFFICE_BINARY_PATH: ${UNO_OFFICE_BINARY_PATH}" \
  && ls -l ${UNO_OFFICE_BINARY_PATH}

# labels
LABEL org.opencontainers.image.source="https://github.com/elifesciences/sciencebeam"
LABEL org.opencontainers.image.revision="${commit}"
LABEL org.opencontainers.image.version="${version}"
