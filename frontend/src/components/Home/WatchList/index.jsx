import { useState, useEffect } from "react";
import "./index.css";
import { Star, Trash2, Activity, Plus, X } from "lucide-react";

export default function Watchlist() {
  const [isOpen, setIsOpen] = useState(false);
  const USER_ID = 1; 
  const [watchlist, setWatchlist] = useState(["AAPL", "NVDA", "2330.TW"]);

  // 1. 將資料源改為 State，以便更新 base (昨收價)
  const [stockData, setStockData] = useState([
    { symbol: "AAPL", name: "Apple Inc.", base: 175.3, domain: "apple.com" },
    { symbol: "GOOG", name: "Alphabet", base: 138.0, domain: "google.com" },
    { symbol: "TSLA", name: "Tesla, Inc.", base: 240.5, domain: "tesla.com" },
    { symbol: "MSFT", name: "Microsoft", base: 420.0, domain: "microsoft.com" },
    { symbol: "AMZN", name: "Amazon", base: 180.0, domain: "amazon.com" },
    { symbol: "NVDA", name: "NVIDIA", base: 890.0, domain: "nvidia.com" },
    { symbol: "2330.TW", name: "TSMC", base: 780.0, domain: "tsmc.com" },
    { symbol: "NFLX", name: "Netflix", base: 600.0, domain: "netflix.com" },
  ]);

  const [prices, setPrices] = useState(() => {
    const initial = {};
    stockData.forEach((s) => {
      initial[s.symbol] = { price: s.base, change: 0, pct: 0 };
    });
    return initial;
  });

  // 2. 連接後端：抓取資料並計算昨收價 (base)
  useEffect(() => {
    fetch(`/api/v1/watchlists/${USER_ID}`)
      .then((res) => res.json())
      .then((response) => {
        if (response.code === 1) {
          const apiData = response.data;

          // 更新 base (反推昨收價)
          setStockData((prevData) =>
            prevData.map((stock) => {
              const match = apiData.find((d) => d.ticker === stock.symbol);
              if (match) {
                const realBase = match.price / (1 + match.change / 100);
                return { ...stock, base: realBase };
              }
              return stock;
            })
          );

          // 更新初始顯示價格
          setPrices((prevPrices) => {
            const nextPrices = { ...prevPrices };
            apiData.forEach((d) => {
              if (prevPrices[d.ticker]) {
                const realBase = d.price / (1 + d.change / 100);
                nextPrices[d.ticker] = {
                  price: d.price,
                  change: d.price - realBase,
                  pct: d.change,
                };
              }
            });
            return nextPrices;
          });
        }
      })
      .catch((err) => console.error("Fetch error:", err));
  }, []);

  // 3. 模擬跳動 (使用更新後的 stockData)
  useEffect(() => {
    const interval = setInterval(() => {
      setPrices((prev) => {
        const next = { ...prev };
        stockData.forEach((stock) => {
          const move = (Math.random() - 0.5) * (stock.base * 0.002);
          const newPrice = Math.max(0.01, prev[stock.symbol].price + move);
          next[stock.symbol] = {
            price: newPrice,
            change: newPrice - stock.base,
            pct: ((newPrice - stock.base) / stock.base) * 100,
          };
        });
        return next;
      });
    }, 1500);
    return () => clearInterval(interval);
  }, [stockData]);

  // --- 操作功能 ---
  const addToWatchlist = (symbol) => {
    if (!watchlist.includes(symbol)) setWatchlist([...watchlist, symbol]);
  };
  const removeFromWatchlist = (symbol) => {
    setWatchlist(watchlist.filter((s) => s !== symbol));
  };
  const availableToAdd = stockData.filter((s) => !watchlist.includes(s.symbol));
  const getLogoUrl = (domain) => `https://logo.clearbit.com/${domain}?size=60`;

  return (
    <>
      <button className="watchlist-toggle-btn" onClick={() => setIsOpen(true)}>
        <Star size={20} />
      </button>

      <div className={`watchlist-drawer-container ${isOpen ? "open" : ""}`} onClick={() => setIsOpen(false)}>
        <div className="watchlist-drawer" onClick={(e) => e.stopPropagation()}>
          <div className="watchlist-header">
            <div className="watchlist-title-group">
              <h2 className="watchlist-title">
                <Activity size={18} color="#ef4444" />
                My Watchlist
              </h2>
              <p className="watchlist-subtitle">Live Market Data</p>
            </div>
            <button className="close-btn" onClick={() => setIsOpen(false)}>
              <X size={20} />
            </button>
          </div>

          <div className="watchlist-content">
            {watchlist.length === 0 ? (
              <div className="watchlist-empty">No stocks watching</div>
            ) : (
              watchlist.map((symbol) => {
                const s = stockData.find((d) => d.symbol === symbol);
                const p = prices[symbol];
                if (!s || !p) return null;

                return (
                  <div key={symbol} className="watchlist-item">
                    <div className="item-left">
                      <img src={getLogoUrl(s.domain)} alt={s.symbol} className="item-logo" />
                      <div>
                        <div className="item-symbol">{symbol}</div>
                        <div className="item-name">{s.name}</div>
                      </div>
                    </div>
                    <div className="item-right">
                      
                      {/* --- 修改重點：價格顯示區塊 --- */}
                      <div className="price-group">
                        
                        {/* 1. 新增：昨收價 (灰白字) */}
                        <span className="price-prev">
                          Prev: {s.base.toFixed(2)}
                        </span>

                        {/* 2. 原有：最新價 */}
                        <span className={`price-val ${p.change >= 0 ? "text-up" : "text-down"}`}>
                          {p.price.toFixed(2)}
                        </span>

                        {/* 3. 原有：漲跌幅 */}
                        <span className={`price-pct ${p.change >= 0 ? "bg-up" : "bg-down"}`}>
                          {p.pct > 0 ? "+" : ""}{p.pct.toFixed(2)}%
                        </span>

                      </div>
                      
                      <button onClick={() => removeFromWatchlist(symbol)} className="delete-btn">
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          <div className="watchlist-add-section">
            <p className="add-label">Add Symbols</p>
            <div className="add-grid">
              {availableToAdd.map((s) => (
                <div key={s.symbol} className="add-item" onClick={() => addToWatchlist(s.symbol)}>
                  <span className="add-symbol">{s.symbol}</span>
                  <Plus size={14} className="add-icon" />
                </div>
              ))}
              {availableToAdd.length === 0 && <span className="text-gray-500 text-xs">All added</span>}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}