FROM python:3.7

COPY Main.py .

COPY aax.py .

COPY bitforex.py .

COPY binance.py .

COPY bitforex.py .

COPY hitbtc.py .

COPY Investor.py .

COPY requirements.txt .

RUN pip install -r requirements.txt

CMD ["python", "./Main.py"]