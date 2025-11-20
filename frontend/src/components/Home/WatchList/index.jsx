import { useState } from "react";
import "./index.css";
import { Star, Trash } from "lucide-react";

export default function Watchlist() {
  const [isOpen, setIsOpen] = useState(false);
  const myStocks = [
    { symbol: "TSLA", price: "240.50", change: "+1.2%", isUp: true },
    { symbol: "AAPL", price: "192.30", change: "-0.5%", isUp: false },
    { symbol: "NVDA", price: "460.10", change: "+3.1%", isUp: true },
    { symbol: "GOOG", price: "135.60", change: "+0.2%", isUp: true },
    { symbol: "GOOG", price: "135.60", change: "+0.2%", isUp: true },
    { symbol: "GOOG", price: "135.60", change: "+0.2%", isUp: true },
    { symbol: "GOOG", price: "135.60", change: "+0.2%", isUp: true },
    { symbol: "GOOG", price: "135.60", change: "+0.2%", isUp: true },
  ];

  return (
    <>
      <button
        className="watchlist-toggle-btn"
        onClick={() => setIsOpen(!isOpen)}
      >
        <Star />
      </button>
      <div className={`watchlist-drawer ${isOpen ? "open" : ""}`}>
        <header className="watch-list-header">
          <h4 style={{ color: "white" }}>My Watchlist</h4>
          <button className="add-stock-list-item">+</button>
        </header>
        <table className="watch-list-table">
          <thead>
            <tr>
              <td>Ticker</td>
              <td>Lastest Price</td>
              <td>Change %</td>
            </tr>
          </thead>
          <tbody>
            {myStocks.map((stock) => (
              <tr key={stock.symbol}>
                <td>{stock.symbol}</td>
                <td>{stock.price}</td>
                <td
                  className={stock.isUp ? "positive-change" : "negative-change"}
                >
                  {stock.change}
                  <button className="delete-stock-list-item">
                    <Trash size={16} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}