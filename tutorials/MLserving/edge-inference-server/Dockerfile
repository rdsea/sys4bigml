FROM python:3.9
RUN apt update
RUN apt install -y git wget make build-essential manpages-dev python3-pip vim

WORKDIR /inference

RUN git clone https://github.com/pjreddie/darknet.git
RUN cd darknet

WORKDIR /inference/darknet
RUN make

RUN wget https://pjreddie.com/media/files/yolov3-tiny.weights

COPY requirements.txt requirements.txt
RUN ["mkdir", "/inference/temp"]

RUN pip3 install -r requirements.txt
COPY . . 
# Injecting customized python version for calling the object detection

RUN apt-get update
RUN apt-get -o Dpkg::Options::="--force-confmiss" install -y --reinstall netbase

EXPOSE 4002
# ENTRYPOINT ["tail", "-f", "/dev/null"]
CMD ["gunicorn", "-k", "eventlet", "-b", "0.0.0.0:4002", "server:app"]