# MarketPulse

The **MarketPulse** project is a system for collecting, processing, and analyzing data on cryptocurrency market pairs from exchanges, as well as generating reports and sending them to Telegram. 

## Description

The project consists of several main modules:

1. **`market_data_fetcher.py`**: Executes requests to the API of exchanges to obtain data on market pairs.
2. **`market_reporter.py`**: Generates reports on changes in market pairs and sends them to Telegram.
3. **`old_data_remover.py`**: Removes old records from the database.
4. **`main.py`**: The main script for running all project processes.

## Project structure.

### 1. `market_data_fetcher.py`.

The module is responsible for:

- **Fetching data from the API**: The `fetch_exchange_market_data()` function makes requests to the API to obtain information about coins on the exchange.
- Saving data**: The `save_response_to_file()` function saves the received data to a JSON file.
- Processing and saving data to the database**: The `process_market_pair_data()` function processes the data and saves it to the database in the form of market pairs.

### 2. `market_reporter.py`.

The module is responsible for:

- **Report generation**: The `generate_reports()` function generates reports based on the received data, filtering significant changes.
- **Formatting messages for Telegram**: The `format_telegram_messages()` function formats messages for sending.
- **Sending messages to Telegram**: The `send_telegram_message()` function sends the generated messages to Telegram.

### 3. `old_data_remover.py`.

The module is responsible for:

- **deleting old records**: The `delete_old_records()` function deletes records from the database that are older than the specified number of hours.

### 4. `main.py`.

The main script that:

- **Starts the data collection process**: The `fetch_market_data()` function starts the data collection.
- **Generates reports and sends them to Telegram**: The `generate_reports()` function starts generating reports.
- **Removes old records from the database**: The `remove_old_records()` function regularly deletes old records.

## Configuration.

The project configuration is stored in the `.env` file:

```env
# database config
DATABASE_URL="mysql+mysqlconnector://user:password@host/table_name”

# telegram config
TG_TOKEN=<your_tg_token>.
TG_CHAT_ID=<your_tg_group_id>

# data parser
PARSING_LIMIT=500
EXCHANGES=binance,mexc,bybit

# telegram reports
THRESHOLD=10.0
CHECK_INTERVAL=600

# old record remover
HOURS_TO_REMOVE=3
REMOVE_CHECK_INTERVAL=3600
```

## Startup

Use `main.py` to run the project:

```bash
python main.py
```

This script runs all the main processes in three separate threads:

- Collecting data from the API.
- Generating and sending reports.
- Deleting old records from the database.

## License

This project is licensed under the MIT License.
