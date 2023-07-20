FROM python:3.8.17-bullseye

ENV AWS_DEFAULT_REGION=us-east-1

# update all the libraries in ubuntu
RUN apt-get update -y
RUN apt-get install -y git openssh-client
RUN mkdir -p -m 0600 ~/.ssh && ssh-keyscan github.com >> ~/.ssh/known_hosts

# install virtual env
RUN python -m pip install --upgrade pip

RUN pip install tensorflow==2.10.1
RUN pip install tqdm==4.59.0
RUN pip install scipy==1.8.1
RUN pip install scikit-learn==1.2.2