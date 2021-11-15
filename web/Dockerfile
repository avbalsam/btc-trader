FROM python:3.8

ENV APP_HOME /web

WORKDIR $APP_HOME

COPY app.py .

RUN true

COPY requirements.txt .

RUN pip install -r requirements.txt

ENTRYPOINT ["python app.py"]
