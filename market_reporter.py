import os
import requests
from time import sleep
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_
from loguru import logger
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from database import MarketPairData, SessionLocal

load_dotenv()


class MarketPairRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_market_pairs_in_timeframe(self, start_time: datetime, end_time: datetime) -> list[[MarketPairData]]:
        """Отримуємо всі ринкові пари за певний інтервал часу."""
        return (
            self.session.query(MarketPairData)
            .filter(and_(MarketPairData.timestamp >= start_time, MarketPairData.timestamp <= end_time))
            .order_by(MarketPairData.market_pair, MarketPairData.timestamp)
            .all()
        )


def filter_significant_changes(
        market_data: list[MarketPairData], threshold: float, processed_market_pairs: set[str]) -> list[dict]:
    """
    Фільтрує пари, ціна яких змінилася більше ніж на threshold% за інтервал.
    Залишає торгові пари, які ще не були оброблені.
    """
    significant_changes = []
    market_pairs = {}

    for data in market_data:
        if data.market_pair not in market_pairs:
            market_pairs[data.market_pair] = [data]
        else:
            market_pairs[data.market_pair].append(data)

    for market_pair, records in market_pairs.items():
        if market_pair in processed_market_pairs:
            continue

        initial_price = records[0].price
        for record in records[1:]:
            price_change = ((record.price - initial_price) / initial_price) * 100
            if abs(price_change) >= threshold:
                significant_changes.append({
                    'market_pair': f"{record.market_pair} ({record.exchange_name})",
                    'price': record.price,
                    'change_percentage': price_change,
                    'timestamp': record.timestamp,
                    'market_url': record.market_url
                })
                processed_market_pairs.add(record.market_pair)  # Додаємо пару в оброблені
                break

    return significant_changes


def generate_reports(session: Session, threshold: float) -> dict[str, dict[str, list[dict]]]:
    """
    Генеруємо звіти по ринкових парах для інтервалів часу, уникаючи повторення пар.
    """
    current_time = datetime.now(timezone.utc)
    intervals = {
        '10 min': current_time - timedelta(minutes=10),
        '30 min': current_time - timedelta(minutes=30),
        '60 min': current_time - timedelta(hours=1),
        '6 hours': current_time - timedelta(hours=6),
        '12 hours': current_time - timedelta(hours=12),
        '24 hours': current_time - timedelta(days=1)
    }

    reports = {}
    processed_market_pairs = set()  # Множина для зберігання оброблених торгових пар

    repository = MarketPairRepository(session)
    exchanges = {record.exchange_name for record in session.query(MarketPairData.exchange_name).distinct()}

    logger.info(f"Exchanges found: {exchanges}")

    for exchange in exchanges:
        exchange_reports = {}
        for interval_name, start_time in sorted(intervals.items(), key=lambda x: x[1], reverse=True):
            market_data = repository.get_market_pairs_in_timeframe(start_time, current_time)
            logger.debug(f"Market data for {exchange} between {start_time} and {current_time}: [ {len(market_data)} ]")

            # Фільтруємо дані по біржі
            filtered_data = [data for data in market_data if data.exchange_name == exchange]
            logger.debug(f"Filtered data for {exchange} {interval_name}: [ {len(filtered_data)} ]")

            report = filter_significant_changes(filtered_data, threshold, processed_market_pairs)
            logger.debug(f"Report for {exchange} in interval {interval_name}: [ {len(report)} ]")

            if report:
                exchange_reports[interval_name] = report

        if exchange_reports:
            reports[exchange] = exchange_reports

    return reports


def format_telegram_messages(
        reports: dict[str, dict[str, list[dict[str, str | float | datetime]]]]) -> dict[str, str]:
    """
    Формуємо текстові повідомлення для кожної біржі і кожного інтервалу часу.
    URL буде інтегровано в назву торгової пари, щоб зробити її клікабельною у HTML форматі.
    """
    messages = {}

    for exchange, intervals in reports.items():
        message = f"Біржа: {exchange}\n"
        for interval, changes in intervals.items():
            message += f"\nІнтервал {interval}:\n-------------------------\n"
            for change in changes:
                price = f"{change['price']:.6f}"  # Форматування до 6 десяткових знаків
                change_percentage = f"{change['change_percentage']:.2f}"
                message += (
                    f"<a href='{change['market_url']}'>{change['market_pair']}</a>:\n"
                    f"{change_percentage}% за {price} USD\n"
                )
        messages[exchange] = message

    return messages


def send_telegram_message(token: str, chat_id: str, message: str) -> None:
    """
    Надсилаємо повідомлення в Telegram з HTML форматуванням.
    """
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }

    response = None

    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        logger.info('Message sent successfully!')
        logger.debug(f"Response content: {response.text}")  # Виведення вмісту відповіді
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
        logger.debug(f"Response content: {response.text}")  # Виведення вмісту відповіді
    except Exception as err:
        logger.error(f"Other error occurred: {err}")
    else:
        if response:
            logger.debug(f"Response content: {response.text}")  # Виведення вмісту відповіді


def run_report_generation(threshold: float, check_interval: int, telegram_token: str, telegram_chat_id: str) -> None:
    """
    Основна функція, яка керує процесом збору даних, формування звітів та відправлення повідомлень у Telegram.
    """
    while True:
        with SessionLocal() as session:
            reports = generate_reports(session, threshold)
            if reports:
                messages = format_telegram_messages(reports)
                for message in messages.values():
                    send_telegram_message(telegram_token, telegram_chat_id, message)
        sleep(check_interval)


if __name__ == '__main__':
    logger.info("Starting report generation")
    run_report_generation(
        threshold=10.0,
        check_interval=600,
        telegram_token=os.getenv('TG_TOKEN'),
        telegram_chat_id="-1002281937136"
    )
