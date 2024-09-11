import sys
import time
from datetime import datetime, timedelta, timezone

from loguru import logger
from sqlalchemy import delete
from sqlalchemy.orm import Session
from database import MarketPairData, SessionLocal

logger.remove()
logger.add(sys.stdout, colorize=True)


def delete_old_records(session: Session, days: int = 7) -> None:
    """
    Видаляє записи з таблиці MarketPairData, які старіші ніж вказана кількість днів.

    Аргументи:
        session (Session): Сесія бази даних.
        days (int): Кількість днів для фільтрації старих записів. За замовчуванням 7 днів.
    """
    threshold_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Формуємо запит для видалення записів
    stmt = delete(MarketPairData).where(MarketPairData.timestamp < threshold_date)

    try:
        # Виконуємо запит
        result = session.execute(stmt)
        session.commit()
        logger.info("Видалено {count} записів старіших ніж {days} днів", count=result.rowcount, days=days)
    except Exception as e:
        session.rollback()
        logger.error("Помилка при видаленні старих записів: {error}", error=e)
        raise e


if __name__ == '__main__':
    while True:
        with SessionLocal() as db_session:
            delete_old_records(session=db_session, days=2)
        time.sleep(3600)
