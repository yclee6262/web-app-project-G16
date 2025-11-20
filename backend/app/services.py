from app.db import get_db
import pymysql
from collections import defaultdict

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