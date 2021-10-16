FROM python:3.9.7

RUN useradd -u myuser

USER myuser

RUN whoami

ADD Main.py .

ADD Exchange.py .

ADD Investor.py .

ADD requirements.txt .

RUN pip install -r requirements.txt

CMD ["python", "./Main.py"]