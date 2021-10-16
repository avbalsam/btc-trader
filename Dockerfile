FROM python:3.8

ADD Main.py .

ADD Exchange.py .

ADD Investor.py .

ADD requirements.txt .

RUN pip install -r requirements.txt

CMD ["python", "./Main.py"]