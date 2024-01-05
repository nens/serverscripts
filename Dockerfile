FROM ghcr.io/fkrull/docker-multi-python:bionic
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN mkdir /code
WORKDIR /code
