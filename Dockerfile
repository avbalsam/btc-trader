FROM python:3.9.7

ADD Main.py .

ADD Exchange.py .

ADD Investor.py .

ADD requirements.txt .

RUN pip install -r requirements.txt

RUN pip3 install websocket

RUN pip3 install websocket-client

CMD ["python", "./Main.py"]