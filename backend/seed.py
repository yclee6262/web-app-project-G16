import pymysql
import yfinance as yf
import datetime
from tqdm import tqdm
import pandas as pd
import os

DB_CONFIG = {
    'host': os.environ.get('MYSQL_HOST', '127.0.0.1'),
    'port': 3306,
    'user': os.environ.get('MYSQL_USER', 'root'),
    'password': os.environ.get('MYSQL_PASSWORD', 'your_password'),
    'database': os.environ.get('MYSQL_DB', 'investment_platform'),
    'cursorclass': pymysql.cursors.DictCursor
}

# --- 2. 要抓取的股票清單 ---
TICKERS_TO_SEED = ['AAPL', 'GOOG', 'TSLA', 'MSFT', 'AMZN', 'NVDA', '2330.TW', 'NFLX', 'META', 'INTC', 'SOFI', 'CRWV', 'COST', 'FIG']

# --- 3. 抓取歷史資料的日期範圍 ---
START_DATE = (datetime.date.today() - datetime.timedelta(days=5*365)).strftime('%Y-%m-01') # 5 年前
END_DATE = datetime.date.today().strftime('%Y-%m-%d') # 今天


def seed_database():
    """
    主執行函數：抓取資料並寫入資料庫
    """
    connection = None
    print('🚀 開始執行 Python 資料填充腳本...')
    
    try:
        connection = pymysql.connect(**DB_CONFIG)
        print('✅ 資料庫連線成功！')

        with connection.cursor() as cursor:
            
            # -- 步驟 A: 填充 `Securities` (股票基本資料) --
            print(f'\n🔍 正在抓取 {len(TICKERS_TO_SEED)} 檔股票的基本資料...')
            for ticker_symbol in tqdm(TICKERS_TO_SEED, desc="處理 Securities"):
                try:
                    ticker_obj = yf.Ticker(ticker_symbol)
                    info = ticker_obj.info
                    security_data = {
                        'ticker': ticker_symbol,
                        'name': info.get('shortName', info.get('longName', 'N_A')),
                        'exchange': info.get('exchange', 'N_A')
                    }
                    sql = """
                        INSERT INTO Securities (ticker_symbol, name, exchange) 
                        VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE 
                            name = VALUES(name), 
                            exchange = VALUES(exchange);
                    """
                    cursor.execute(sql, (
                        security_data['ticker'],
                        security_data['name'],
                        security_data['exchange']
                    ))
                except Exception as e:
                    print(f'\n  ❌ 抓取 {ticker_symbol} 基本資料時出錯: {e}')
            print('✅ `Securities` 資料表填充完畢！')


            # -- 步驟 B: 填充 `HistoricalPrices` (歷史價格) --
            print(f'\n⏳ 正在抓取 5 年份的歷史價格 (這可能需要一點時間)...')

            for ticker_symbol in tqdm(TICKERS_TO_SEED, desc="處理 HistoricalPrices"):
                try:
                    
                    history_df = yf.download(
                        ticker_symbol,
                        start=START_DATE,
                        end=END_DATE,
                        interval="1d",
                        auto_adjust=False, # 保持 False 才能拿到 'Adj Close'
                        progress=False     
                    )

                    if history_df.empty:
                        print(f'\n  ⚠️ 找不到 {ticker_symbol} 的歷史資料，跳過...')
                        continue

                    # 使用 (欄位, 股票代號) 這種元組 (Tuple) 來當作 Key
                    close_key = ('Close', ticker_symbol)
                    adj_close_key = ('Adj Close', ticker_symbol)
                    volume_key = ('Volume', ticker_symbol)

                    # 檢查這些 key 是否存在
                    if not all(key in history_df.columns for key in [close_key, adj_close_key, volume_key]):
                        print(f'\n  ⚠️ {ticker_symbol} 回傳的欄位不完整，跳過...')
                        continue

                    # 在 dropna 中使用元組 (Tuple) Key
                    history_df.dropna(
                        subset=[close_key, adj_close_key, volume_key], 
                        inplace=True
                    )

                    if history_df.empty:
                        print(f'\n  ⚠️ {ticker_symbol} 的資料全是 NaN，跳過...')
                        continue
                        
                    # 準備批次插入 (Bulk Insert) 的資料
                    values_to_insert = []
                    for date, row in history_df.iterrows():
                        formatted_date = date.strftime('%Y-%m-%d')
                        
                        # 【重大修正 3】
                        # 在存取 row 資料時，使用元組 (Tuple) Key
                        values_to_insert.append((
                            ticker_symbol,
                            formatted_date,
                            row[close_key],      # `close` 欄位
                            row[adj_close_key],  # `adjusted_close` 欄位
                            row[volume_key]
                        ))
                    
                    if not values_to_insert:
                        continue

                    sql = """
                        INSERT INTO HistoricalPrices (ticker_symbol, date, `close`, adjusted_close, volume) 
                        VALUES (%s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE 
                            `close` = VALUES(`close`), 
                            adjusted_close = VALUES(adjusted_close), 
                            volume = VALUES(volume);
                    """
                    
                    cursor.executemany(sql, values_to_insert)

                except KeyError as e:
                    print(f'\n  ❌ 抓取 {ticker_symbol} 時發生欄位錯誤 (KeyError): {e} - 欄位未找到')
                except Exception as e:
                    print(f'\n  ❌ 抓取 {ticker_symbol} 歷史價格時出錯: {type(e).__name__} {e}')

            print('✅ `HistoricalPrices` 資料表填充完畢！')

        connection.commit()
        print('\n🎉 資料庫事務已提交，所有資料寫入成功！')

    except pymysql.Error as e:
        print(f'❌ 資料庫連線或操作失敗: {e}')
        if connection:
            connection.rollback()
            print('🚫 資料庫事務已回滾。')
    
    finally:
        if connection:
            connection.close()
            print('🚪 資料庫連線已關閉。')

# --- 執行腳本 ---
if __name__ == "__main__":
    seed_database()