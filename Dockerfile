FROM python:3.12

WORKDIR /app

COPY requirements.txt requirements.txt
COPY old_data_remover.py market_reporter.py market_data_fetcher.py database.py start.py ./
COPY .env .env

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "start.py"]