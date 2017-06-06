FROM python:3.5

RUN mkdir /app

COPY alice /app/alice
COPY data /app/data
COPY gunicorn /app/gunicorn
COPY mi /app/mi
COPY users /app/users
COPY wins /app/wins
COPY fixturedb /app/fixturedb

COPY requirements.txt /app/requirements.txt
COPY manage.py /app/manage.py
COPY start.sh /app/start.sh

WORKDIR /app
RUN pip install -r /app/requirements.txt

EXPOSE 8000
CMD ./start.sh
