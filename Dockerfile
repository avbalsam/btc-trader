FROM python:3.9.7

ADD Main.py .

ADD Exchange.py .

ADD Investor.py .

ADD requirements.txt .

RUN pip install websocket-client

RUN pip install -r requirements.txt

CMD ["python", "./Main.py"]