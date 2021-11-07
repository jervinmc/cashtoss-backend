FROM python:3.8-slim

ENV PYTHONUNBUFFERED 1

RUN apt-get -y update && apt-get -y upgrade && apt-get -y install libmariadb-dev-compat

WORKDIR /app

COPY . /app

RUN pip3 --no-cache-dir install -r requirements.txt                                                                            

EXPOSE 5000

ENTRYPOINT  ["python3"]

CMD ["app.py"]