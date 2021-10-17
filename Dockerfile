FROM python:3

ADD Main.py .

ADD aax.py .

ADD bitforex.py .

ADD binance.py .

ADD bitforex.py .

ADD hitbtc.py .

ADD Investor.py .

ADD requirements.txt .

RUN pip install -r requirements.txt

CMD ["python", "./Main.py"]