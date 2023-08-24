FROM python:latest
WORKDIR /application

COPY app app
COPY instance instance
COPY requirements.txt requirements.txt
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 5000

RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y supervisor

CMD [ "/usr/bin/supervisord" ]