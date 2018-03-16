FROM python:2.7.14-stretch
ARG tensorflow_version=1.4.0
ARG apache_beam_version=2.2.0
WORKDIR /srv/sciencebeam
RUN virtualenv venv
RUN venv/bin/pip install tensorflow==${tensorflow_version}
RUN venv/bin/pip install apache-beam==${apache_beam_version}
RUN venv/bin/pip install https://github.com/elifesciences/sciencebeam-gym/archive/develop.zip
COPY sciencebeam /srv/sciencebeam/sciencebeam
COPY xslt /srv/sciencebeam/xslt
COPY *.cfg *.conf *.sh *.in *.txt *.py /srv/sciencebeam/
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install -r requirements.py2.txt