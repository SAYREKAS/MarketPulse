import os
from time import sleep
from threading import Thread

from dotenv import load_dotenv

from database import SessionLocal
from market_data_fetcher import process_market_pair_data
from market_reporter import run_report_generation
from old_data_remover import delete_old_records

load_dotenv()


def fetch_market_data():
    exchanges = os.getenv('EXCHANGES').split(',')
    process_market_pair_data(coin_limit=int(os.getenv('PARSING_LIMIT')), exchanges=exchanges, save=False)


def generate_reports():
    run_report_generation(
        threshold=float(os.getenv('THRESHOLD')),
        check_interval=int(os.getenv('CHECK_INTERVAL')),
        telegram_token=os.getenv('TG_TOKEN'),
        telegram_chat_id=os.getenv('TG_CHAT_ID')
    )


def remove_old_records():
    while True:
        with SessionLocal() as db_session:
            delete_old_records(session=db_session, days=int(os.getenv('DAYS_TO_REMOVE')))
        sleep(int(os.getenv('REMOVE_CHECK_INTERVAL')))


if __name__ == '__main__':
    # Створюємо потоки
    fetch_thread = Thread(target=fetch_market_data)
    report_thread = Thread(target=generate_reports)
    removal_thread = Thread(target=remove_old_records)

    # Запускаємо потоки
    fetch_thread.start()
    report_thread.start()
    removal_thread.start()

    # Очікуємо завершення потоків (необов'язково)
    fetch_thread.join()
    report_thread.join()
    removal_thread.join()
