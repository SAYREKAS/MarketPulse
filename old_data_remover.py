import sys
import time
from datetime import datetime, timedelta, timezone

from loguru import logger
from sqlalchemy import delete
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from database import MarketPairData, SessionLocal

load_dotenv()

logger.remove()
logger.add(sys.stdout, colorize=True)


def delete_old_records(session: Session, hours: int = 7) -> None:
    """
    Видаляє записи з таблиці MarketPairData, які старіші ніж вказана кількість годин.

    Аргументи:
        session (Session): Сесія бази даних.
        hours (int): Кількість годин для фільтрації старих записів. За замовчуванням 7 годин.
    """
    threshold_date = datetime.now(timezone.utc) - timedelta(hours=hours)

    # Формуємо запит для видалення записів
    stmt = delete(MarketPairData).where(MarketPairData.timestamp < threshold_date)

    try:
        # Виконуємо запит
        result = session.execute(stmt)
        session.commit()
        logger.info("Видалено {count} записів старіших ніж {hours} годин", count=result.rowcount, hours=hours)

    except Exception as e:
        session.rollback()
        logger.error("Помилка при видаленні старих записів: {error}", error=e)
        raise e


if __name__ == '__main__':
    while True:
        with SessionLocal() as db_session:
            delete_old_records(session=db_session, hours=3)
        time.sleep(3600)
