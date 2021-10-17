FROM python:3.6

COPY Main.py .

RUN true

COPY aax.py .

RUN true

COPY bitforex.py .

RUN true

COPY binance.py .

RUN true

COPY bitforex.py .

RUN true

COPY hitbtc.py .

RUN true

COPY Investor.py .

RUN true

COPY requirements.txt .

RUN true

RUN pip install -r requirements.txt

CMD ["python", "./Main.py"]