from flask import Blueprint, jsonify, request
from app.db import get_db
import pymysql
import app.services as services

# 建立符合 /api/v1 規格的 Blueprint
api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# ------------------------------------------------------------------
# API: User (符合 user.md 規格)
# ------------------------------------------------------------------

@api_v1.route('/users/signup', methods=['POST'])
def user_signup():
    """
    API: userSignUp
    使用 username 和 password 註冊
    """
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"code": 0, "message": "Missing username or password"}), 400

    username = data['username']
    password = data['password']
    

    db = get_db()
    cursor = db.cursor()

    try:
        # 1. 檢查 username 是否已被使用
        cursor.execute("SELECT user_id FROM Users WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({"code": 0, "message": "Username already exists"}), 409


        # 3. 儲存新使用者
        sql = "INSERT INTO Users (username, password_hash) VALUES (%s, %s)"
        cursor.execute(sql, (username, password))
        db.commit()

        #
        return jsonify({"code": 1, "message": "account successfully created"}), 201

    except pymysql.MySQLError as e:
        db.rollback()
        return jsonify({"code": 0, "message": f"Database error: {e}"}), 500
    finally:
        cursor.close()


@api_v1.route('/users/login', methods=['POST'])
def user_login():
    """
    API: userSignIn
    使用 username 和 password 登入
    """
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"code": 0, "message": "Missing username or password"}), 400

    username = data['username']
    password = data['password']

    db = get_db()
    cursor = db.cursor()

    try:
        # 1. 尋找使用者
        cursor.execute("SELECT user_id, password_hash, username FROM Users WHERE username = %s", (username,))
        user = cursor.fetchone()

        # 2. (安全!) 檢查密碼雜湊
        if user and user['password_hash'] == password:
            # 密碼正確
            return jsonify({
                "data": {
                    "userId": user['user_id'],
                    "userName": user['username'],
                },
                "code": 1,
                "message": "account successfully login"
            }), 200
        else:
            # 使用者不存在或密碼錯誤
            return jsonify({
                "data": {},
                "code": 0,
                "message": "account failed to be login" # (typo fixed)
            }), 401

    except pymysql.MySQLError as e:
        return jsonify({"data": {}, "code": 0, "message": f"Database error: {e}"}), 500
    finally:
        cursor.close()

# ------------------------------------------------------------------
# API: Asset
# ------------------------------------------------------------------
@api_v1.route('/assets', methods=['GET'])
def getAssets():
    """
    API: getAssets
    取得所有資產資料
    """
    try:
        print("debug")
        assets_data = services.get_all_stock_tickers()
        return jsonify({
            "data": assets_data,
            "code": 1,
            "message": "assets retrieved successfully"
        }), 200
    except Exception as e:
        return jsonify({
            "data": [],
            "code": 0,
            "message": f"An unexpected error occurred: {e}"
        }), 500

@api_v1.route('/assets/price/<string:ticker_symbol>', methods=['GET'])
def getAssetHistoricalPrices(ticker_symbol):
    """
    API: getAssetHistoricalPrices
    取得特定資產的歷史價格資料(過去一年)
    """
    try:
        history = services.get_security_history(ticker_symbol)
        if not history:
            return jsonify({
                "data": {},
                "code": 0,
                "message": "Asset not found or no history"
            }), 404
            
        return jsonify({
            "data": {
                "assetName": ticker_symbol,
                "historicalPrice": history
            },
            "code": 1,
            "message": "the historical price is successfully retrieved"
        }), 200
    except Exception as e:
        return jsonify({"data": {}, "code": 0, "message": str(e)}), 500

# ------------------------------------------------------------------
# API: Portfolio
# ------------------------------------------------------------------
@api_v1.route('/portfolio/<int:user_id>', methods=['GET'])
def getUserPortfolio(user_id):
    """
    API: getUserPortfolio
    取得特定使用者的投資組合資料
    """
    try:
        portfolio_data = services.get_user_portfolios_data(user_id)
        if not portfolio_data:
            return jsonify({
                "data": [],
                "code": 1,
                "message": "no portfolios found for the user"
            }), 200
        return jsonify({
            "data": portfolio_data,
            "code": 1,
            "message": "portfolios retrieved successfully"
        }), 200
    except pymysql.MySQLError as e:
        return jsonify({
            "data": [],
            "code": 0,
            "message": f"Database error: {e}"
        }), 500
    except Exception as e:
        # 處理 Pandas 或其他潛在的運算錯誤
        return jsonify({
            "data": [],
            "code": 0,
            "message": f"An unexpected error occurred: {e}"
        }), 500

@api_v1.route('/portfolio/<int:portfolio_id>', methods=['POST'])
def updatePortfolio(portfolio_id):
    """
    API: updatePortfolio
    更新特定投資組合的資料 (新增/修改投資標的)
    """
    data = request.get_json()
    if not data:
        return jsonify({"code": 0, "message": "Missing request body"}), 400
    
    assets_map = data.get(str(portfolio_id))
    # (防呆) 如果上面都沒抓到，但 data 本身就是 { "TSMC": 10 } 這種格式
    if assets_map is None:
        # 檢查 data 的 values 是否都是數字 (代表直接傳了資產 Map)
        is_direct_map = all(isinstance(v, (int, float)) for k, v in data.items())
        if is_direct_map:
            assets_map = data

    if assets_map is None or not isinstance(assets_map, dict):
        return jsonify({
            "code": 0, 
            "message": "Invalid format. Expected { 'portfolioId': { 'TICKER': quantity } }"
        }), 400
    
    # 轉換成服務層需要的格式
    # Map: { "TSMC": 10, "AAPL": 90 }
    # List: [ {"ticker": "TSMC", "quantity": 10}, {"ticker": "AAPL", "quantity": 90} ]
    normalized_assets = []
    for ticker, quantity in assets_map.items():
        # 過濾掉可能混入的非股票欄位
        if ticker in ['id', 'portfolioId', 'userId']: 
            continue
            
        normalized_assets.append({
            "ticker": ticker,
            "quantity": float(quantity)
        })

    try:
        # 3. 呼叫 Service 執行更新 (全量覆蓋)
        result = services.update_portfolio_assets(portfolio_id, normalized_assets)
        
        # 提交交易
        get_db().commit()

        if result is None:
             return jsonify({"data": {}, "code": 0, "message": "Portfolio not found"}), 404

        # 4. 回傳成功回應 (符合您提供的格式)
        return jsonify({
            "data": result,
            "code": 1,
            "message": "Portfolio successfully added"
        }), 200

    except pymysql.MySQLError as e:
        get_db().rollback()
        return jsonify({"data": {}, "code": 0, "message": f"Database error: {e}"}), 500
    except Exception as e:
        get_db().rollback()
        return jsonify({"data": {}, "code": 0, "message": f"Error: {e}"}), 500

@api_v1.route('/portfolio/create', methods=['POST'])
def createPortfolio():
    """
    API: createPortfolio
    建立新的投資組合
    Request Body: { "userId": 1, "name": "My New Portfolio", "assets": ... }
    """
    data = request.get_json()
    if not data or 'userId' not in data or 'name' not in data:
        return jsonify({"code": 0, "message": "Missing userId or name"}), 400

    user_id = data['userId']
    name = data['name']
    
    normalized_assets = []
    raw_assets = data.get('assets')

    if raw_assets:
        # 情況 A: List 格式 [ {"ticker": "AAPL", "quantity": 10}, ... ]
        if isinstance(raw_assets, list):
            normalized_assets = raw_assets
        
        # 情況 B: Map 格式 { "AAPL": 10, "TSMC": 20 }
        elif isinstance(raw_assets, dict):
            for ticker, qty in raw_assets.items():
                normalized_assets.append({
                    "ticker": ticker,
                    "quantity": float(qty)
                })

    try:
        # 呼叫 Service
        result = services.create_user_portfolio(user_id, name, normalized_assets)
        
        # 提交交易
        get_db().commit()

        if result is None:
            return jsonify({"code": 0, "message": "User not found"}), 404

        return jsonify({
            "data": result,
            "code": 1,
            "message": "Portfolio successfully created"
        }), 201

    except pymysql.MySQLError as e:
        get_db().rollback()
        return jsonify({"data": {}, "code": 0, "message": f"Database error: {e}"}), 500
    except Exception as e:
        get_db().rollback()
        return jsonify({"data": {}, "code": 0, "message": f"Error: {e}"}), 500

@api_v1.route('/portfolio/<int:portfolio_id>', methods=['DELETE'])
def deletePortfolio(portfolio_id):
    """
    API: deletePortfolio
    刪除特定投資組合
    """
    try:
        # 呼叫 Service 執行刪除
        success = services.delete_portfolio_by_id(portfolio_id)
        
        # 提交交易 (讓刪除生效)
        get_db().commit()

        if success:
            # 刪除成功
            return jsonify({
                "code": 1,
                "message": "portfolio successfully deleted"
            }), 200
        else:
            # 找不到 ID (刪除失敗)
            return jsonify({
                "code": 0,
                "message": "portfolio fail to be deleted"  # (可能是 ID 不存在)
            }), 404

    except pymysql.MySQLError as e:
        get_db().rollback()
        return jsonify({"code": 0, "message": f"Database error: {e}"}), 500
    except Exception as e:
        get_db().rollback()
        return jsonify({"code": 0, "message": f"Error: {e}"}), 500

@api_v1.route('/portfolio/performance/<int:portfolio_id>', methods=['GET'])
def getPortfolioPerformance(portfolio_id):
    """
    API: getPortfolioPerformance
    取得特定投資組合的績效資料
    """
    try:
        # 呼叫 Service
        result = services.get_portfolio_performance_history(portfolio_id)
        
        if result is None:
            return jsonify({
                "data": {},
                "code": 0,
                "message": "Portfolio not found"
            }), 404

        # 回傳成功回應 (符合 docs/portfolio.md 格式)
        return jsonify({
            "data": result,
            "code": 1,
            "message": "portfolio history successfully retrieved"
        }), 200

    except Exception as e:
        return jsonify({"data": {}, "code": 0, "message": str(e)}), 500

@api_v1.route('/portfolio/simulation/<int:portfolio_id>', methods=['GET'])
def simulatePortfolio(portfolio_id):
    """
    API: simulatePortfolio
    模擬特定投資組合的資產配置
    """
    try:
        # 呼叫 Service 執行模擬
        percentiles = services.simulate_portfolio_growth(portfolio_id)
        
        if percentiles is None:
            return jsonify({
                "data": [],
                "code": 0,
                "message": "Fail to stimulate (No history or portfolio empty)"
            }), 400

        # 轉換為前端需要的格式 array of objects
        # 格式: [ {"10th": [...]}, {"25th": [...]}, ... ]
        formatted_val = []
        # 依照常見順序排列
        for key in ["10th", "25th", "50th", "75th", "90th"]:
            if key in percentiles:
                formatted_val.append({key: percentiles[key]})

        return jsonify({
            "data": {
                "portfolioId": portfolio_id,
                "name": f"Portfolio {portfolio_id}", # (可選: 再去 DB 查真實名稱)
                "portfolioVal": formatted_val
            },
            "code": 1,
            "message": "successfully stimulate"
        }), 200

    except Exception as e:
        return jsonify({"data": [], "code": 0, "message": str(e)}), 500

@api_v1.route('/portfolio/recommendation/<int:portfolio_id>', methods=['GET'])
def recommendPortfolio(portfolio_id):
    """
    API: recommendPortfolio
    為特定投資組合提供資產配置建議
    """
    try:
        # 呼叫 Service
        recommendation = services.generate_portfolio_recommendation(portfolio_id)
        
        if recommendation is None:
            return jsonify({
                "data": {},
                "code": 0,
                "message": "Insufficient data to generate recommendation (Need at least 2 days of history)"
            }), 400
            
        return jsonify({
            "data": recommendation,
            "code": 1,
            "message": "Recommendation generated successfully"
        }), 200
        
    except Exception as e:
        return jsonify({"data": {}, "code": 0, "message": str(e)}), 500

# -------------------------------------------------------------------
# API: Watchlist
# -------------------------------------------------------------------
@api_v1.route('/watchlists/<int:user_id>', methods=['GET'])
def getUserWatchlist(user_id):
    """
    API: getUserWatchlist
    取得使用者的關注清單
    """
    try:
        watchlist_data = services.get_user_watchlist(user_id)
        return jsonify({
            "data": watchlist_data,
            "code": 1,
            "message": "watchlist retrieved successfully"
        }), 200
    except pymysql.MySQLError as e:
        return jsonify({
            "data": [],
            "code": 0,
            "message": f"Database error: {e}"
        }), 500
    except Exception as e:
        return jsonify({
            "data": [],
            "code": 0,
            "message": f"An unexpected error occurred: {e}"
        }), 500
    
@api_v1.route('/watchlists/<int:user_id>', methods=['POST'])
def addStockWatchListItem(user_id):
    """
    API: addStockWatchListItem
    新增關注股票
    Request Body: { "ticker": "2330.TW" }
    """
    data = request.get_json()
    if not data or 'ticker' not in data:
        return jsonify({"data": {}, "code": 0, "message": "Missing ticker"}), 400
        
    ticker = data['ticker']
    
    try:
        # 呼叫 Service 新增並取得股票資訊
        added_stock_info = services.add_watchlist_item(user_id, ticker)
        
        # 提交交易
        get_db().commit()
        
        return jsonify({
            "data": added_stock_info,
            "code": 1,
            "message": "stock successfully added"
        }), 200
        
    except Exception as e:
        get_db().rollback()
        return jsonify({"data": {}, "code": 0, "message": str(e)}), 500
    
@api_v1.route('/watchlists/<int:user_id>/<string:ticker>', methods=['DELETE'])
def deleteWatchListItem(user_id, ticker):
    """
    API: deleteWatchListItem
    移除關注股票
    """
    try:
        success = services.remove_watchlist_item(user_id, ticker)
        get_db().commit()
        
        if success:
            return jsonify({
                "code": 1,
                "message": "stock successfully deleted"
            }), 200
        else:
            return jsonify({
                "code": 0,
                "message": "Stock not found in watchlist"
            }), 404 # 或者 200，視前端需求而定，這裡依據 doc 失敗回傳 code 0
            
    except Exception as e:
        get_db().rollback()
        return jsonify({"code": 0, "message": str(e)}), 500