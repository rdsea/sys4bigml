FROM python:3.10
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

# Injecting customized python version for calling the object detection

RUN apt-get update
RUN apt-get -o Dpkg::Options::="--force-confmiss" install -y --reinstall netbase
RUN pip install eventlet==0.33.0 https://github.com/benoitc/gunicorn/archive/refs/heads/master.zip#egg=gunicorn==20.1.0
RUN apt install -y uuid-runtime
RUN pip install qoa4ml==0.3.14

COPY . . 

EXPOSE 4002
RUN chmod +x /inference/darknet/start.sh
ENTRYPOINT ["./start.sh"]
# ENTRYPOINT ["tail", "-f", "/dev/null"]