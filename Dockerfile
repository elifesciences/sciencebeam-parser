FROM python:2.7.14-stretch
ENV PROJECT_HOME=/srv/sciencebeam

WORKDIR ${PROJECT_HOME}
RUN virtualenv venv

COPY requirements.prereq.txt ${PROJECT_HOME}/
RUN venv/bin/pip install -r requirements.prereq.txt

ARG sciencebeam_gym_commit
RUN venv/bin/pip install https://github.com/elifesciences/sciencebeam-gym/archive/${sciencebeam_gym_commit}.zip

COPY requirements.txt ${PROJECT_HOME}/
RUN venv/bin/pip install -r requirements.txt

COPY requirements.py2.txt ${PROJECT_HOME}/
RUN venv/bin/pip install -r requirements.py2.txt

COPY sciencebeam /srv/sciencebeam/sciencebeam
COPY xslt /srv/sciencebeam/xslt
COPY *.cfg *.conf *.sh *.in *.txt *.py /srv/sciencebeam/
