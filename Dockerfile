# syntax=docker/dockerfile:experimental
FROM python:3.8-slim

ENV AWS_DEFAULT_REGION=us-east-1
#ADD ./ ./
#WORKDIR ./

# update all the libraries in ubuntu
RUN apt-get update -y
RUN apt-get install -y git openssh-client
RUN mkdir -p -m 0600 ~/.ssh && ssh-keyscan github.com >> ~/.ssh/known_hosts

# install virtual env
COPY ./requirements.txt ./
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt
