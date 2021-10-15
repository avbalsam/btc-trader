FROM python:3

ADD Main.py .

ADD Exchange.py .

ADD Investor.py .

ADD requirements.txt .

RUN pip install -r requirements.txt

CMD ["python", "./my_script.py"]