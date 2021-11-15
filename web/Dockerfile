FROM python:3.8

ENV APP_HOME /app

WORKDIR $APP_HOME

COPY ./app/app.py .

RUN true

COPY ./app/requirements.txt .

RUN pip install -r requirements.txt

ENTRYPOINT ["python app.py"]
