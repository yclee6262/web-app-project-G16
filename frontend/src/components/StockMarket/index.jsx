import "./index.css";
import TopStock from "./TopStock";
import StockLineChart from "./StockLineChart";
import StockMarketCap from "./StockMarketCap";

export default function StockMarket() {
  const marketCapData = {
    marketCap: 2.5e12,
    percentChange: 1.2,
    marketRecentCapData: { yesterday: 2.48e12, lastWeek: 2.45e12, lastMonth: 2.4e12 },
  };
  return (
    <div className="stock-market">
      <h1>Stock Market Overview</h1>
      <p className="stock-market-description">
        Stay updated with the latest trends and insights in the stock market.
      </p>
      <TopStock />
      <main className="stock-market-main">
        <StockMarketCap data={marketCapData} />
        <StockLineChart className="stock-line-chart"/>
      </main>
    </div>
  );
}
