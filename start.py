import os
import random
from threading import Thread
from time import sleep, localtime, strftime

from loguru import logger
from dotenv import load_dotenv
from database import SessionLocal
from old_data_remover import delete_old_records
from market_reporter import run_report_generation
from market_data_fetcher import process_market_pair_data

load_dotenv()


def is_within_schedule() -> bool:
    """Перевіряє, чи знаходиться поточний час в рамках заданого графіка."""
    start_time = os.getenv('START_TIME')
    end_time = os.getenv('END_TIME')
    current_time = strftime("%H:%M", localtime())

    if start_time <= current_time <= end_time:
        return True

    logger.info(f"Current time {current_time} is outside the schedule ({start_time} - {end_time}).")
    return False


def fetch_market_data():
    """Отримує дані ринку в межах робочого часу."""
    exchanges = os.getenv('EXCHANGES').split(',')

    while True:
        if is_within_schedule():
            process_market_pair_data(coin_limit=int(os.getenv('PARSING_LIMIT')), exchanges=exchanges, save=False)

        sleep(random.uniform(400, 600))


def generate_reports():
    """Генерує звіти в межах робочого часу."""

    while True:
        if is_within_schedule():
            run_report_generation(
                threshold=float(os.getenv('THRESHOLD')),
                telegram_token=os.getenv('TG_TOKEN'),
                telegram_chat_id=os.getenv('TG_CHAT_ID')
            )

        sleep(int(os.getenv('CHECK_INTERVAL')))


def remove_old_records():
    """Видаляє старі записи постійно."""

    while True:
        if is_within_schedule():
            with SessionLocal() as db_session:
                delete_old_records(session=db_session, hours=int(os.getenv('HOURS_TO_REMOVE')))

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
