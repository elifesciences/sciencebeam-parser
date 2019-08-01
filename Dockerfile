FROM python:3.5.7-stretch

RUN apt-get update
RUN apt-get install -y libreoffice-writer

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

ARG commit
ARG version
COPY docker ./docker
RUN ./docker/set-version.sh "${version}" "${commit}"

RUN useradd -ms /bin/bash sciencebeam
USER sciencebeam
ENV HOME=/home/sciencebeam

# labels
LABEL org.opencontainers.image.source="https://github.com/elifesciences/sciencebeam"
LABEL org.opencontainers.image.revision="${commit}"
LABEL org.opencontainers.image.version="${version}"
