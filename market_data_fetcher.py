import os
import sys
import json
import time
import random
from typing import Optional
from datetime import datetime

import requests
from requests import get
from loguru import logger
from sqlalchemy import insert
from sqlalchemy.orm import Session
from fake_useragent import UserAgent
from pydantic import BaseModel, ValidationError

from database import SessionLocal, MarketPairData

logger.remove()
logger.add(sys.stdout, colorize=True)


class MarketPairQuote(BaseModel):
    id: str
    price: float
    volume24h: float
    depthPositiveTwo: float
    depthNegativeTwo: float


class MarketPair(BaseModel):
    rank: int
    exchangeId: int
    exchangeName: str
    exchangeSlug: str
    outlierDetected: int
    priceExcluded: int
    volumeExcluded: int
    marketId: int
    marketPair: str
    category: str
    marketUrl: str
    marketScore: str
    marketReputation: float
    baseSymbol: str
    baseCurrencyId: int
    baseCurrencyName: str
    baseCurrencySlug: str
    quoteSymbol: str
    quoteCurrencyId: int
    price: float
    volumeUsd: float
    effectiveLiquidity: Optional[float] = None
    lastUpdated: datetime
    quote: float
    volumeBase: float
    volumeQuote: float
    feeType: str
    depthUsdNegativeTwo: float
    depthUsdPositiveTwo: float
    volumePercent: float
    isVerified: int
    quotes: list[MarketPairQuote]
    type: str


class ExchangeQuote(BaseModel):
    id: str
    derivativeVolume: float
    spotVolume: float
    totalVolume24h: float


class ExchangeData(BaseModel):
    id: int
    name: str
    slug: str
    numMarketPairs: int
    marketPairs: list[MarketPair]
    sort: str
    direction: str
    quotes: list[ExchangeQuote]


class Status(BaseModel):
    timestamp: datetime
    error_code: str
    error_message: str
    elapsed: str
    credit_count: int


class ResponseData(BaseModel):
    data: ExchangeData
    status: Status


def fetch_exchange_market_data(coin_limit: int, exchange: str, save: bool = False) -> ResponseData | bool:
    """
    Робимо запит до API CoinMarketCap для отримання інформації про монети на біржі та зберігаємо її в JSON файл.

    Аргументи:
        coin_limit (int): Кількість монет для запиту.
        exchange (str): Назва біржі для отримання даних.
        save (bool): Зберігає відповідь у JSON файл, якщо True.

    Повертає:
        ResponseData або False: Якщо запит вдалий, повертається об'єкт ResponseData.
        У разі помилки або відсутності відповіді — повертається False.
    """
    api_url: str = (
        f"https://api.coinmarketcap.com/data-api/v3/"
        f"exchange/market-pairs/latest"
        f"?slug={exchange}"
        f"&category=spot"
        f"&start=1"
        f"&limit={coin_limit}"
    )

    ua: UserAgent = UserAgent()
    logger.debug("Формуємо URL запиту: {url}", url=api_url)

    try:
        response = get(api_url, headers={'User-Agent': ua.random})
        logger.success("Запит до API виконано зі статусом {status_code}", status_code=response.status_code)

        if response.status_code == 200:
            response_json = response.json()
            logger.success("Отримано валідну відповідь від API CoinMarketCap")

            if save:
                save_response_to_file(response_json)

            try:
                data = ResponseData(**response_json)
                logger.success("Дані успішно валідовані за допомогою Pydantic")
                return data

            except ValidationError as e:
                logger.error("Помилка валідації даних: {error}", error=e)
                return False

        else:
            logger.warning("Помилка при підключенні до API, статус код - {status_code}",
                           status_code=response.status_code)
            return False

    except requests.exceptions.ConnectionError:
        logger.error("Помилка з'єднання з API.")
        return False


def save_response_to_file(response_json: dict) -> None:
    """
    Зберігає відповідь API у JSON файл.

    Аргументи:
        response_json (dict): Відповідь API у форматі словника.
    """
    with open('coin_info.json', 'w', encoding='utf8') as file:
        json.dump(response_json, file, ensure_ascii=False, indent=4)
    logger.info("Відповідь API збережена у 'coin_info.json'")


def save_market_pair_data_bulk(session: Session, market_pairs_list: list[dict]) -> None:
    """
    Пакетне збереження інформації про ринкові пари у базу даних.

    Аргументи:
        session (Session): Сесія бази даних.
        market_pairs_list (list[dict]): Список словників з інформацією про ринкові пари.
    """
    try:
        stmt = insert(MarketPairData).values(market_pairs_list)
        session.execute(stmt)
        session.commit()
        logger.success("Дані успішно збережені у базу даних.")

    except Exception as e:
        session.rollback()
        logger.error("Помилка при збереженні даних у базу: {error}", error=e)
        raise e


def process_market_pair_data(coin_limit: int, exchanges: list[str], save: bool) -> None:
    """
    Основна функція для отримання даних про ринкові пари для кількох бірж та їх збереження у базу даних.
    """
    while True:
        for exchange in exchanges:
            info = fetch_exchange_market_data(coin_limit=coin_limit, exchange=exchange, save=save)

            if info:
                market_pairs = info.data.marketPairs
                timestamp = info.status.timestamp

                data = [
                    {
                        'market_pair': row.marketPair,
                        'exchange_name': row.exchangeName,
                        'category': row.category,
                        'market_url': row.marketUrl,
                        'price': row.price,
                        'timestamp': timestamp
                    }
                    for row in market_pairs
                ]

                with SessionLocal() as db:
                    save_market_pair_data_bulk(session=db, market_pairs_list=data)
                    time.sleep(random.uniform(60, 120))

        # Затримка між циклами
        time.sleep(random.uniform(400, 700))


if __name__ == '__main__':
    process_market_pair_data(
        coin_limit=500,
        exchanges=os.getenv('EXCHANGES').split(','),
        save=False
    )
