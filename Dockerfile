FROM python:3.9.7

ADD Main.py .

ADD Exchange.py .

ADD Investor.py .

ADD requirements.txt .

RUN pip install -r requirements.txt

RUN pip uninstall websocket

RUN pip uninstall websocket-client

RUN pip install websocket-client

CMD ["python", "./Main.py"]