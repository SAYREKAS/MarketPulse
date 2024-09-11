import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Створюємо базу для моделей SQLAlchemy
Base = declarative_base()

# Підключення до бази даних MySQL
DATABASE_URL = os.getenv('DATABASE_URL')

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Модель для збереження інформації про ринкові пари
class MarketPairData(Base):
    __tablename__ = 'market_pairs'

    id = Column(Integer, primary_key=True)
    market_pair = Column(String(100), index=True)
    exchange_name = Column(String(50))
    category = Column(String(50))
    market_url = Column(String(255))
    price = Column(Float)
    timestamp = Column(DateTime)

    def __repr__(self) -> str:
        return (f"<MarketPairData(market_pair={self.market_pair}, category={self.category}, "
                f"price={self.price}, timestamp={self.timestamp})>")


if __name__ == '__main__':
    # Створення таблиці у базі даних
    Base.metadata.create_all(bind=engine)
