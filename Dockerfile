FROM python:2.7.14-stretch
ARG tensorflow_version=1.4.0
WORKDIR /srv/sciencebeam
RUN virtualenv venv
RUN venv/bin/pip install tensorflow==${tensorflow_version}
RUN venv/bin/pip install https://github.com/elifesciences/sciencebeam-gym/archive/develop.zip
COPY sciencebeam /srv/sciencebeam/sciencebeam
COPY *.conf *.sh *.in *.txt *.py /srv/sciencebeam/
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install -r requirements.py2.txt