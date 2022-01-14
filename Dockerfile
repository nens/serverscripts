FROM fkrull/multi-python:focal
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN mkdir /code
WORKDIR /code
