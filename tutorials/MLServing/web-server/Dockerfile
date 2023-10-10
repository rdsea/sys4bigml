FROM python:3.9

WORKDIR /web-server
COPY ./requirements.txt .
RUN apt update
RUN apt install -y wget vim gcc python3-dev
RUN pip install -r requirements.txt
RUN pip install eventlet==0.33.0 https://github.com/benoitc/gunicorn/archive/refs/heads/master.zip#egg=gunicorn==20.1.0
COPY . .

EXPOSE 5000
# USER nobody
# ENTRYPOINT ["tail", "-f", "/dev/null"]
CMD ["gunicorn", "-k", "eventlet", "-b", "0.0.0.0:5000", "web_server:app"]
