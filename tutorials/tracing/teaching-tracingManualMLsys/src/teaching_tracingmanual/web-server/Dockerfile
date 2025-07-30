FROM python:3.10

WORKDIR /web-server
COPY ./requirements.txt .
RUN apt update
RUN apt install -y wget vim gcc python3-dev
RUN pip install -r requirements.txt
RUN pip install eventlet==0.33.0 https://github.com/benoitc/gunicorn/archive/refs/heads/master.zip#egg=gunicorn==20.1.0
RUN apt install -y uuid-runtime
RUN pip install qoa4ml==0.3.10
COPY . .

EXPOSE 5000
# USER nobody
RUN chmod +x /web-server/start.sh
ENTRYPOINT ["./start.sh"]
# ENTRYPOINT ["tail", "-f", "/dev/null"]