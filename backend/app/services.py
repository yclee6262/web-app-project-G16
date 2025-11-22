from app.db import get_db
import pymysql
from collections import defaultdict
import pandas as pd
from datetime import date, timedelta
import numpy as np

def get_all_stock_tickers():
    """
    輔助函式: 獲取所有股票代號列表。
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT ticker_symbol FROM Securities")
    tickers = [row['ticker_symbol'] for row in cursor.fetchall()]
    cursor.close()
    return tickers

def get_security_history(ticker):
    """
    [Asset API] 取得單一股票的歷史價格
    """
    db = get_db()
    cursor = db.cursor()
    sql = "SELECT date, adjusted_close FROM HistoricalPrices WHERE ticker_symbol = %s ORDER BY date ASC"
    cursor.execute(sql, (ticker,))
    data = cursor.fetchall()
    
    # 回傳格式: {"2024-01-01": 100.5, "2024-01-02": 101.0, ...}
    return {row['date'].strftime('%Y-%m-%d'): float(row['adjusted_close']) for row in data}

def get_user_portfolios_data(user_id):
    """
    [功能 1] 獲取特定使用者所有投資組合的數據，包括最新價格。
    """
    db = get_db()
    cursor = db.cursor()
    
    # 1. 獲取使用者所有的 Portfolios 和 PortfolioItems
    sql = """
        SELECT 
            p.portfolio_id, 
            p.name, 
            pi.ticker_symbol, 
            pi.quantity
        FROM Portfolios p
        JOIN PortfolioItems pi ON p.portfolio_id = pi.portfolio_id
        WHERE p.user_id = %s
        ORDER BY p.portfolio_id, pi.ticker_symbol
    """
    cursor.execute(sql, (user_id,))
    portfolio_data = cursor.fetchall()

    if not portfolio_data:
        cursor.close()
        return []

    # 2. 處理數據並收集所有需要的股票代號
    portfolio_map = defaultdict(lambda: {'assets': []})
    all_tickers = set()

    for row in portfolio_data:
        pid = row['portfolio_id']
        ticker = row['ticker_symbol']
        
        # 建構 portfolio 結構
        portfolio_map[pid]['portfolioId'] = pid
        portfolio_map[pid]['name'] = row['name']
        portfolio_map[pid]['assets'].append({
            'ticker': ticker,
            'quantity': float(row['quantity'])
        })
        all_tickers.add(ticker)

    # 3. 獲取所有 unique 股票的「最新」收盤價 (price is lattest price in db)
    latest_prices = {}
    if all_tickers:
        ticker_placeholders = ', '.join(['%s'] * len(all_tickers))
        
        # 這是最有效率的 SQL 查詢，用於獲取每個 ticker 的最新價格
        sql_latest_price = f"""
            SELECT 
                t1.ticker_symbol, 
                t1.close AS price
            FROM HistoricalPrices t1
            INNER JOIN (
                SELECT ticker_symbol, MAX(date) AS max_date
                FROM HistoricalPrices
                WHERE ticker_symbol IN ({ticker_placeholders})
                GROUP BY ticker_symbol
            ) t2 ON t1.ticker_symbol = t2.ticker_symbol AND t1.date = t2.max_date
        """
        
        cursor.execute(sql_latest_price, tuple(all_tickers))
        # 將結果轉換為 { 'AAPL': 150.00, 'GOOG': 1300.00 } 的字典
        latest_prices = {row['ticker_symbol']: float(row['price']) for row in cursor.fetchall()}
    
    cursor.close()

    # 4. 組合最終結果
    final_result = []
    for pid, portfolio in portfolio_map.items():
        updated_assets = []
        for asset in portfolio['assets']:
            ticker = asset['ticker']
            price = latest_prices.get(ticker, 0.0) # 找不到最新價格時使用 0.0
            
            # 格式化輸出
            updated_assets.append({
                'ticker': ticker,
                'price': round(price, 4), 
                'quantity': asset['quantity']
            })
        
        final_result.append({
            'portfolioId': portfolio['portfolioId'],
            'name': portfolio['name'],
            'assets': updated_assets
        })
        
    return final_result

def update_portfolio_assets(portfolio_id, new_assets_list):
    """
    [功能 2] 更新投資組合的資產 (全量更新：刪除舊的 -> 插入新的)
    new_assets_list: list of dict, e.g., [{'ticker': 'AAPL', 'quantity': 10}, ...]
    """
    db = get_db()
    cursor = db.cursor()
    
    # 1. 檢查 Portfolio 是否存在
    cursor.execute("SELECT portfolio_id FROM Portfolios WHERE portfolio_id = %s", (portfolio_id,))
    if not cursor.fetchone():
        return None # Portfolio not found

    # 2. 刪除該 Portfolio 所有的舊項目 (PortfolioItems)
    cursor.execute("DELETE FROM PortfolioItems WHERE portfolio_id = %s", (portfolio_id,))
    
    # 3. 準備插入新項目
    if not new_assets_list:
        # 如果清單是空的，代表清空資產，直接回傳
        return {'portfolioId': portfolio_id, 'quantity': {}}

    # 4. 處理每一筆新資產
    # (我們需要確保 Ticker 存在於 Securities 表中，否則會報 Foreign Key 錯誤)
    
    # 4a. 收集所有涉及的 Ticker
    tickers = set(item['ticker'] for item in new_assets_list)
    
    # 4b. 找出資料庫中還沒有的 Ticker
    if tickers:
        format_strings = ','.join(['%s'] * len(tickers))
        cursor.execute(f"SELECT ticker_symbol FROM Securities WHERE ticker_symbol IN ({format_strings})", tuple(tickers))
        existing_tickers = set(row['ticker_symbol'] for row in cursor.fetchall())
        missing_tickers = tickers - existing_tickers
        
        # 4c. 自動插入缺少的 Ticker (避免 FK 報錯)
        if missing_tickers:
            # 簡單插入，Name 暫時用 Ticker 代替，Exchange 設為 Unknown
            insert_security_sql = "INSERT INTO Securities (ticker_symbol, name, exchange) VALUES (%s, %s, 'Unknown')"
            cursor.executemany(insert_security_sql, [(t, t) for t in missing_tickers])

    # 5. 批次插入 PortfolioItems
    insert_items_sql = """
        INSERT INTO PortfolioItems (portfolio_id, ticker_symbol, quantity) 
        VALUES (%s, %s, %s)
    """
    values_to_insert = [
        (portfolio_id, item['ticker'], item['quantity']) 
        for item in new_assets_list
    ]
    cursor.executemany(insert_items_sql, values_to_insert)
    
    # 6. 建構回傳格式 (符合 API 文件: quantity: { ticker: qty })
    quantity_map = {item['ticker']: item['quantity'] for item in new_assets_list}
    
    return {
        'portfolioId': portfolio_id,
        'quantity': quantity_map
    }

def create_user_portfolio(user_id, name, assets_list):
    """
    [功能 3] 建立新的投資組合
    """
    db = get_db()
    cursor = db.cursor()

    # 1. 檢查使用者是否存在 (防呆)
    cursor.execute("SELECT user_id FROM Users WHERE user_id = %s", (user_id,))
    if not cursor.fetchone():
        return None # User not found

    # 2. 插入新的 Portfolio
    sql_create = "INSERT INTO Portfolios (user_id, name) VALUES (%s, %s)"
    cursor.execute(sql_create, (user_id, name))
    
    # 3. 取得新產生的 portfolio_id
    new_portfolio_id = cursor.lastrowid

    # 4. 如果有初始資產，直接呼叫 update_portfolio_assets 來處理
    # (這樣可以重用「自動新增 Securities」和「批次插入」的邏輯)
    assets_result = {}
    if assets_list:
        # 注意：這裡是在同一個 transaction 中，所以 update 函式能讀到剛插入的 portfolio
        update_result = update_portfolio_assets(new_portfolio_id, assets_list)
        assets_result = update_result.get('quantity', {})

    # 5. 建構回傳資料
    return {
        "portfolioId": new_portfolio_id,
        "name": name,
        "assets": assets_result # 回傳 {ticker: qty} 格式
    }

def delete_portfolio_by_id(portfolio_id):
    """
    [功能 4] 刪除指定的投資組合
    回傳: True (刪除成功), False (找不到該 ID 或刪除失敗)
    """
    db = get_db()
    cursor = db.cursor()

    # 直接執行刪除指令
    # 由於設定了 ON DELETE CASCADE，這會連同 PortfolioItems 一起刪除
    sql = "DELETE FROM Portfolios WHERE portfolio_id = %s"
    cursor.execute(sql, (portfolio_id,))
    
    # rowcount 會回傳被刪除的列數
    # 如果 > 0 代表有東西被刪除 (成功)
    # 如果 == 0 代表該 portfolio_id 不存在
    affected_rows = cursor.rowcount
    
    return affected_rows > 0

def get_stock_market_data(ticker):
    """
    [Helper] 取得單一股票的「最新價格」與「漲跌幅」
    回傳: { 'ticker': 'AAPL', 'price': 150.0, 'change': 1.5 }
    """
    db = get_db()
    cursor = db.cursor()
    
    # 撈取最近 2 筆股價資料 (為了計算漲跌幅)
    sql = """
        SELECT date, close 
        FROM HistoricalPrices 
        WHERE ticker_symbol = %s 
        ORDER BY date DESC 
        LIMIT 2
    """
    cursor.execute(sql, (ticker,))
    rows = cursor.fetchall()
    
    if not rows:
        return {'ticker': ticker, 'price': 0, 'change': 0}
    
    latest_price = float(rows[0]['close'])
    change_percent = 0.0
    
    # 如果有至少兩天的資料，才能算漲跌幅
    if len(rows) >= 2:
        prev_price = float(rows[1]['close'])
        if prev_price != 0:
            change_percent = ((latest_price - prev_price) / prev_price) * 100
            
    return {
        'ticker': ticker,
        'price': round(latest_price, 2),
        'change': round(change_percent, 2)
    }

def get_user_watchlist(user_id):
    """
    [WatchList API] 取得使用者的關注清單 (包含價格資訊)
    """
    db = get_db()
    cursor = db.cursor()
    
    # 1. 找出該使用者關注的所有股票代號
    sql = "SELECT ticker_symbol FROM WatchListItems WHERE user_id = %s"
    cursor.execute(sql, (user_id,))
    watchlist_items = cursor.fetchall()
    
    result = []
    for item in watchlist_items:
        ticker = item['ticker_symbol']
        # 2. 逐一取得每支股票的行情 (未來可優化為批次查詢)
        stock_data = get_stock_market_data(ticker)
        result.append(stock_data)
        
    return result

def get_portfolio_performance_history(portfolio_id):
    """
    [功能 5] 取得投資組合的歷史績效走勢 (回傳給前端畫圖用)
    回傳格式: { "name": "組合名稱", "history": { "2023-01-01": 1000.0, ... } }
    """
    db = get_db()
    cursor = db.cursor()

    # 1. 取得 Portfolio 名稱 (確認存在)
    cursor.execute("SELECT name FROM Portfolios WHERE portfolio_id = %s", (portfolio_id,))
    row = cursor.fetchone()
    if not row:
        return None
    portfolio_name = row['name']

    # 2. 取得該組合的持股
    cursor.execute("SELECT ticker_symbol, quantity FROM PortfolioItems WHERE portfolio_id = %s", (portfolio_id,))
    items = cursor.fetchall()
    
    # 如果是空組合
    if not items:
        return {
            "name": portfolio_name,
            "history": {}
        }

    tickers = [item['ticker_symbol'] for item in items]
    # 轉為 float 避免 Decimal 運算錯誤
    quantities = {item['ticker_symbol']: float(item['quantity']) for item in items}

    # 3. 撈取這些股票的「所有」歷史價格
    format_strings = ','.join(['%s'] * len(tickers))
    sql = f"""
        SELECT date, ticker_symbol, adjusted_close 
        FROM HistoricalPrices 
        WHERE ticker_symbol IN ({format_strings})
        ORDER BY date ASC
    """
    cursor.execute(sql, tuple(tickers))
    price_rows = cursor.fetchall()

    if not price_rows:
        return {
            "name": portfolio_name,
            "history": {}
        }

    # 4. 使用 Pandas 計算每日總價值
    df = pd.DataFrame(price_rows)
    
    # 確保價格是 float
    df['adjusted_close'] = df['adjusted_close'].astype(float)
    
    # 轉置表格: Index=Date, Columns=Ticker, Values=Price
    df_pivot = df.pivot(index='date', columns='ticker_symbol', values='adjusted_close')
    
    # 填充缺失值 (Forward Fill)，並刪除仍有空值的行 (例如某支股票尚未上市的早期日期)
    df_pivot = df_pivot.ffill().dropna()

    # 計算總價值: Sum(Price * Quantity)
    df_pivot['total_value'] = 0.0
    for ticker in quantities:
        if ticker in df_pivot.columns:
            df_pivot['total_value'] += df_pivot[ticker] * quantities[ticker]

    # 5. 轉換為字典格式 { "YYYY-MM-DD": 1234.56 }
    # (Series index 是 date 物件，需要轉字串)
    history_dict = {
        date.strftime('%Y-%m-%d'): round(val, 2)
        for date, val in df_pivot['total_value'].items()
    }

    return {
        "name": portfolio_name,
        "history": history_dict
    }

# ---------------------------------------------------------
# WatchList (關注清單) 相關服務
# ---------------------------------------------------------

def add_watchlist_item(user_id, ticker):
    """
    [WatchList API] 新增關注股票
    """
    db = get_db()
    cursor = db.cursor()
    
    # 1. 確保股票存在於 Securities 表 (避免 FK 錯誤)
    # (如果不存在，先插入一個暫時的紀錄)
    cursor.execute("SELECT ticker_symbol FROM Securities WHERE ticker_symbol = %s", (ticker,))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO Securities (ticker_symbol, name, exchange) VALUES (%s, %s, 'Unknown')",
            (ticker, ticker)
        )
    
    # 2. 插入 WatchListItems (使用 IGNORE 避免重複關注報錯)
    sql = "INSERT IGNORE INTO WatchListItems (user_id, ticker_symbol) VALUES (%s, %s)"
    cursor.execute(sql, (user_id, ticker))
    
    # 3. 回傳該股票的最新資訊 (符合 API 需求)
    return get_stock_market_data(ticker)

def remove_watchlist_item(user_id, ticker):
    """
    [WatchList API] 移除關注股票
    """
    db = get_db()
    cursor = db.cursor()
    
    sql = "DELETE FROM WatchListItems WHERE user_id = %s AND ticker_symbol = %s"
    cursor.execute(sql, (user_id, ticker))
    
    return cursor.rowcount > 0

# ---------------------------------------------------------
# Simulation (蒙地卡羅模擬) 相關服務
# ---------------------------------------------------------

def get_portfolio_daily_values(portfolio_id, days=252):
    """
    [Helper] 計算某個投資組合「過去 N 天」的每日總價值序列
    用於計算歷史報酬率 (Daily Returns)
    """
    db = get_db()
    cursor = db.cursor()

    # 1. 取得該組合的持股
    cursor.execute("SELECT ticker_symbol, quantity FROM PortfolioItems WHERE portfolio_id = %s", (portfolio_id,))
    items = cursor.fetchall()
    if not items:
        return None

    tickers = [item['ticker_symbol'] for item in items]
    # 【修正 1】在這裡將 quantity (Decimal) 轉為 float
    quantities = {item['ticker_symbol']: float(item['quantity']) for item in items}

    # 2. 撈取這些股票過去 N 天的歷史價格
    # (抓取足夠多的資料以確保填充後有 days 天)
    start_date = (date.today() - timedelta(days=days * 2)).strftime('%Y-%m-%d')
    format_strings = ','.join(['%s'] * len(tickers))
    
    sql = f"""
        SELECT date, ticker_symbol, adjusted_close 
        FROM HistoricalPrices 
        WHERE ticker_symbol IN ({format_strings}) AND date >= %s
        ORDER BY date ASC
    """
    cursor.execute(sql, (*tickers, start_date))
    price_rows = cursor.fetchall()
    
    if not price_rows:
        return None

    # 3. 使用 Pandas 整理數據 (Pivot Table)
    df = pd.DataFrame(price_rows)
    
    # 【修正 2】將 adjusted_close (Decimal) 轉為 float
    df['adjusted_close'] = df['adjusted_close'].astype(float)
    
    # 轉置: Index=Date, Columns=Ticker, Values=Price
    df_pivot = df.pivot(index='date', columns='ticker_symbol', values='adjusted_close')
    
    # 填充缺失值 (Forward Fill) - 使用新版語法
    df_pivot = df_pivot.ffill().dropna()
    
    # 4. 計算每日總價值 (Sum(Price * Quantity))
    df_pivot['total_value'] = 0.0
    for ticker in quantities:
        if ticker in df_pivot.columns:
            # 這裡 quantities[ticker] 已經是 float 了，運算不會報錯
            df_pivot['total_value'] += df_pivot[ticker] * quantities[ticker]
    
    # 取最後 'days' 天的數據
    return df_pivot['total_value'].tail(days).values


def simulate_portfolio_growth(portfolio_id):
    """
    [Simulation API] 執行蒙地卡羅模擬
    """
    # 1. 取得過去 1 年 (約 252 交易日) 的每日價值
    portfolio_values = get_portfolio_daily_values(portfolio_id, days=252)
    
    if portfolio_values is None or len(portfolio_values) < 2:
        return None

    # 2. 計算每日報酬率 (Daily Returns)
    # formula: (today - yesterday) / yesterday
    daily_returns = portfolio_values[1:] / portfolio_values[:-1] - 1

    # 3. 計算平均報酬與變異數
    mean_return = np.mean(daily_returns)
    var_return = np.var(daily_returns)

    # 4. 設定模擬參數 (Geometric Brownian Motion)
    # 假設一年 252 個交易日
    annual_mu = mean_return * 252
    annual_sigma = np.sqrt(var_return * 252)
    
    years = 30
    n_sim = 1000 # (建議先設 1000，跑 10000 會比較久)
    dt = 1 # yearly step (以年為單位步進)
    initial_value = portfolio_values[-1] # 以當前價值為起點

    # 5. 執行蒙地卡羅模擬
    # sim_results shape: (n_sim, years + 1)
    sim_results = np.zeros((n_sim, years + 1))
    sim_results[:, 0] = initial_value

    for t in range(1, years + 1):
        Z = np.random.normal(0, 1, n_sim)
        # GBM 公式: S_t = S_{t-1} * exp((mu - 0.5 * sigma^2)*dt + sigma*sqrt(dt)*Z)
        sim_results[:, t] = sim_results[:, t - 1] * np.exp(
            (annual_mu - 0.5 * annual_sigma**2) * dt + annual_sigma * np.sqrt(dt) * Z
        )

    # 6. 計算百分位數 (Percentiles)
    # axis=0 代表在 "模擬次數" 這個維度上取百分位
    percentiles_map = {
        "10th": np.percentile(sim_results, 10, axis=0).tolist(),
        "25th": np.percentile(sim_results, 25, axis=0).tolist(),
        "50th": np.percentile(sim_results, 50, axis=0).tolist(),
        "75th": np.percentile(sim_results, 75, axis=0).tolist(),
        "90th": np.percentile(sim_results, 90, axis=0).tolist(),
    }

    return percentiles_map

# ... (保留原有的 imports 和 code) ...

# ---------------------------------------------------------
# Recommendation 相關服務
# ---------------------------------------------------------

def get_portfolio_metrics(portfolio_id):
    """
    [Helper] 計算投資組合的關鍵財務指標 (Return, Volatility, Sharpe)
    """
    # 重用我們之前寫好的函式，取得過去一年 (252天) 的數據
    portfolio_values = get_portfolio_daily_values(portfolio_id, days=252)
    
    if portfolio_values is None or len(portfolio_values) < 2:
        return None

    # 計算每日報酬率 (Daily Returns)
    daily_returns = portfolio_values[1:] / portfolio_values[:-1] - 1
    
    # 計算年化指標
    # 假設一年有 252 個交易日
    mean_daily_return = np.mean(daily_returns)
    std_daily_return = np.std(daily_returns)
    
    annual_return = mean_daily_return * 252
    annual_volatility = std_daily_return * np.sqrt(252)
    
    # 計算夏普比率 (Sharpe Ratio)
    # 假設無風險利率 (Risk Free Rate) 為 2% (0.02)
    risk_free_rate = 0.02
    if annual_volatility == 0:
        sharpe_ratio = 0
    else:
        sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility
        
    return {
        "annual_return": round(annual_return, 4),       # 例如 0.1523 (15.23%)
        "annual_volatility": round(annual_volatility, 4), # 例如 0.2015 (20.15%)
        "sharpe_ratio": round(sharpe_ratio, 4)          # 例如 0.65
    }

def generate_portfolio_recommendation(portfolio_id):
    """
    [功能 6 - 進階版] 針對組合內的「個別股票」提供買賣建議
    """
    db = get_db()
    cursor = db.cursor()

    # 1. 取得組合持股
    cursor.execute("SELECT ticker_symbol, quantity FROM PortfolioItems WHERE portfolio_id = %s", (portfolio_id,))
    items = cursor.fetchall()
    
    if not items:
        return None

    tickers = [item['ticker_symbol'] for item in items]
    
    # 2. 撈取這些股票過去 1 年 (252天) 的歷史價格
    start_date = (date.today() - timedelta(days=365)).strftime('%Y-%m-%d')
    format_strings = ','.join(['%s'] * len(tickers))
    
    sql = f"""
        SELECT date, ticker_symbol, adjusted_close 
        FROM HistoricalPrices 
        WHERE ticker_symbol IN ({format_strings}) AND date >= %s
        ORDER BY date ASC
    """
    cursor.execute(sql, (*tickers, start_date))
    price_rows = cursor.fetchall()
    
    if not price_rows:
        return None

    # 3. 使用 Pandas 整理數據
    df = pd.DataFrame(price_rows)
    df['adjusted_close'] = df['adjusted_close'].astype(float)
    df_pivot = df.pivot(index='date', columns='ticker_symbol', values='adjusted_close')
    df_pivot = df_pivot.ffill().dropna() # 確保數據對齊

    if len(df_pivot) < 30: # 資料太少不給建議
        return None

    # 4. 計算個別股票的指標
    stock_metrics = {}
    risk_free_rate = 0.02
    
    for ticker in df_pivot.columns:
        prices = df_pivot[ticker]
        daily_returns = prices.pct_change().dropna()
        
        mean_ret = daily_returns.mean() * 252
        volatility = daily_returns.std() * np.sqrt(252)
        sharpe = (mean_ret - risk_free_rate) / volatility if volatility != 0 else 0
        
        stock_metrics[ticker] = {
            "return": mean_ret,
            "volatility": volatility,
            "sharpe": sharpe
        }

    # 計算「組合平均」指標作為基準線 (Benchmark)
    avg_return = np.mean([m['return'] for m in stock_metrics.values()])
    avg_volatility = np.mean([m['volatility'] for m in stock_metrics.values()])
    avg_sharpe = np.mean([m['sharpe'] for m in stock_metrics.values()])

    # 5. 產生具體建議 (Actionable Insights)
    recommendations = []

    for ticker, m in stock_metrics.items():
        action = "HOLD"
        reason = "表現平穩，建議續抱"
        score = 50 # 0-100 分數

        # --- 賣出邏輯 ---
        if m['return'] < -0.10: # 年化虧損超過 10%
            action = "SELL"
            reason = f"嚴重落後表現 (年化 {m['return']:.1%})，建議停損換股"
            score = 10
        elif m['volatility'] > (avg_volatility * 1.5):
            action = "REDUCE" # 減碼
            reason = f"波動風險過高 ({m['volatility']:.1%})，建議降低持倉比例"
            score = 30
            
        # --- 買入邏輯 ---
        elif m['sharpe'] > (avg_sharpe * 1.2) and m['return'] > 0:
            action = "BUY"
            reason = f"優質資產！夏普值 ({m['sharpe']:.2f}) 顯著高於組合平均，建議加碼"
            score = 90
        elif m['return'] > (avg_return * 1.2) and m['volatility'] < avg_volatility:
            action = "BUY"
            reason = "高報酬低風險的穩健標的，建議增加配置"
            score = 85

        recommendations.append({
            "ticker": ticker,
            "action": action, # BUY, SELL, REDUCE, HOLD
            "reason": reason,
            "metrics": {
                "annual_return": round(m['return'], 4),
                "volatility": round(m['volatility'], 4),
                "sharpe_ratio": round(m['sharpe'], 2)
            }
        })

    # 6. 回傳結構
    return {
        "portfolio_summary": {
            "avg_return": round(avg_return, 4),
            "avg_volatility": round(avg_volatility, 4)
        },
        "suggestions": recommendations
    }