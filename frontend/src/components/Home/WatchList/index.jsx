import { useState, useEffect, useContext } from "react";
import "./index.css";
import { Trash2, Activity, Plus, X, Search } from "lucide-react";
import { StoreContext } from "../../Utils/Context";
import api from "../../api";
import EmptyContent from "../../Utils/EmptyContent";
import { CircleQuestionMark, Loader2 } from "lucide-react";

export default function Watchlist() {
  const domainMp = {
    AAPL: "apple.com",
    GOOG: "google.com",
    TSLA: "tesla.com",
    MSFT: "microsoft.com",
    AMZN: "amazon.com",
    NVDA: "nvidia.com",
    "2330.TW": "tsmc.com",
    NFLX: "netflix.com",
  };

  const { userInfo } = useContext(StoreContext);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const [watchlist, setWatchlist] = useState([]);
  const [allTickers, setAllTickers] = useState([]);
  const [filterTickers, setFilterTickers] = useState([]);
  const fetchWatchlistData = async () => {
    try {
      const response = await api.get(`/watchlists/${userInfo.userId}`);
      const data = response.data.data;
      setWatchlist(data);
    } catch (error) {
      console.error("Fetch error:", error);
    }
  };

  const addWatchListItem = async (symbol) => {
    try {
      setLoading(true);
      await api.post(`/watchlists/${userInfo.userId}`, {
        ticker: symbol,
      });
      setRefresh((prev) => prev ^ 1);
    } catch (error) {
      console.error("Add error:", error);
    } finally {
      setLoading(false);
    }
  };

  const removeWatchListItem = async (symbol) => {
    try {
      setLoading(true);
      await api.delete(`/watchlists/${userInfo.userId}/${symbol}`);
      setRefresh((prev) => prev ^ 1);
    } catch (error) {
      console.error("Remove error:", error);
    } finally {
      setLoading(false);
    }
  };

  const filterTickersFunc = (query) => {
    const filtered = allTickers.filter((ticker) =>
      ticker.toLowerCase().includes(query.toLowerCase())
    );
    setFilterTickers(filtered);
  };

  useEffect(() => {
    if (userInfo.userId) {
      fetchWatchlistData();
    }
  }, [userInfo.userId, refresh]);

  useEffect(() => {
    const fetchTickers = async () => {
      try {
        setLoading(true);
        const response = await api.get("/assets");
        setAllTickers(response.data.data || []);
        setFilterTickers(response.data.data || []);
      } catch (error) {
        console.error("Failed to fetch tickers", error);
        setAllTickers([]);
      } finally {
        setLoading(false);
      }
    };
    fetchTickers();
  }, []);

  useEffect(() => {
    const intervalId = setInterval(() => {
      setWatchlist((watchlist) =>
        watchlist.map((item) => {
          const randomChange = (Math.random() - 0.5) * 2;
          const newPrice = Math.max(0.01, item.price + randomChange);
          const change = newPrice - item.price;
          const pct = (change / item.price) * 100;
          return {
            ...item,
            price: newPrice,
            change: pct,
          };
        })
      );
    }, 1500);

    return () => clearInterval(intervalId);
  }, []);

 const getLogoUrl = (ticker) => {
  return ticker 
    ? `https://img.logo.dev/ticker/${ticker}?token=pk_DDGKtB3bSZKAgmfQgXRBsA` 
    : "";
};

  return (
    <div>
      <button
        className="watchlist-toggle-btn"
        onClick={() => setIsOpen(true)}
        aria-label="Open Watchlist" // Vital for screen readers
      >
        <Activity size={20} color="#4ade80" />
      </button>

      <div
        className={`watchlist-drawer-container ${isOpen ? "open" : ""}`}
        onClick={() => setIsOpen(false)}
      >
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
          <div style={{ height: "470px" }}>
            {loading ? (
              <div className="loading-container">
                <Loader2
                  size={40}
                  color="#636e72"
                  className="loading-spinner"
                />
              </div>
            ) : (
              <>
                {watchlist.length === 0 ? (
                  <EmptyContent
                    icon={<CircleQuestionMark size={40} color="#636e72" />}
                    message={"No stocks watching"}
                    subMessage={"Please add some stocks to your watchlist."}
                  />
                ) : (
                  <div className="watchlist-content">
                    {watchlist.map((item) => {
                      return (
                        <div key={item.symbol} className="watchlist-item">
                          <div className="item-left">
                            <img
                              src={getLogoUrl(item.ticker)}
                              alt={item.ticker}
                              className="item-logo"
                            />
                            <div>
                              <div className="item-symbol">{item.ticker}</div>
                              <div className="item-name">
                                {/* company name here */}
                              </div>
                            </div>
                          </div>

                          <div className="item-right">
                            <div className="price-group">
                              <span
                                className={`price-val ${
                                  item.change >= 0 ? "text-up" : "text-down"
                                }`}
                              >
                                {item.price.toFixed(2)}
                              </span>

                              <span
                                className={`price-pct ${
                                  item.change >= 0 ? "bg-up" : "bg-down"
                                }`}
                              >
                                {item.change > 0 ? "+" : ""}
                                {item.change.toFixed(2)}%
                              </span>
                            </div>

                            <button
                              className="delete-btn"
                              onClick={() => removeWatchListItem(item.ticker)}
                            >
                              <Trash2 size={16} />
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </>
            )}
          </div>

          <div className="watchlist-add-section">
            <header>
              <p className="add-label">Add Symbols</p>
              <div className="add-watch-list-search-box">
                <Search size={16} />
                <input
                  style={{ color: "black", paddingLeft: "6px" }}
                  type="text"
                  onChange={(e) => filterTickersFunc(e.target.value)}
                />
              </div>
            </header>
            <div className="add-grid">
              {filterTickers.map((ticker) => (
                <div
                  className="add-item"
                  key={ticker.ticker}
                  onClick={() => addWatchListItem(ticker)}
                >
                  <span className="add-symbol">{ticker}</span>
                  <Plus size={14} className="add-icon" />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
