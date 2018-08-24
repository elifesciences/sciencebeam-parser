FROM python:2.7.14-stretch

RUN apt-get update
RUN apt-get install -y libreoffice-writer

ENV PROJECT_HOME=/srv/sciencebeam

ENV VENV=${PROJECT_HOME}/venv
RUN virtualenv ${VENV}
ENV PYTHONUSERBASE=${VENV} PATH=${VENV}/bin:$PATH

WORKDIR ${PROJECT_HOME}

COPY requirements.prereq.txt ${PROJECT_HOME}/
RUN pip install -r requirements.prereq.txt

COPY requirements.txt ${PROJECT_HOME}/
RUN pip install -r requirements.txt

COPY requirements.py2.txt ${PROJECT_HOME}/
RUN pip install -r requirements.py2.txt

COPY sciencebeam ${PROJECT_HOME}/sciencebeam
COPY xslt ${PROJECT_HOME}/xslt
COPY *.cfg *.conf *.sh *.in *.txt *.py ${PROJECT_HOME}/
