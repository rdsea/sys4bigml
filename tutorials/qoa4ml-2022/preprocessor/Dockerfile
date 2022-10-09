FROM python:3.9

WORKDIR /proc-server
COPY ./requirements.txt .
RUN apt update
RUN apt install -y wget vim gcc python3-dev
RUN pip install -r requirements.txt
COPY . .

EXPOSE 5000
# USER nobody
# ENTRYPOINT ["tail", "-f", "/dev/null"]
CMD ["gunicorn", "-k", "eventlet", "-b", "0.0.0.0:5000", "preprocessor:app"]
