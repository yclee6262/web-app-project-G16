import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import "./index.css";
import api from "../../api";
import { useMemo, useState, useEffect } from "react";
import EmptyContent from "../../Utils/EmptyContent";
import { CircleQuestionMark, Loader2 } from "lucide-react";

// Helper for currency formatting
const formatCurrency = (value) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(
    value
  );

// Helper for date formatting on X-Axis
const formatDate = (dateStr) => {
  const date = new Date(dateStr);
  return `${date.getMonth() + 1}/${date.getDate()}`;
};

export default function StockLineChart() {
  const [allTickers, setAllTickers] = useState([]);
  const [selectedTicker, setSelectedTicker] = useState("");
  const [stockHistory, setStockHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [timeFilter, setTimeFilter] = useState("1Y"); // Active filter state
  const timeFilterOptions = ["1W", "1M", "3M", "1Y", "ALL"];

  const tickerOptions = useMemo(() => {
    return allTickers.map((ticker) => (
      <option key={ticker} value={ticker}>
        {ticker}
      </option>
    ));
  }, [allTickers]);

  // Fetch Tickers on Mount
  useEffect(() => {
    const fetchTickers = async () => {
      try {
        const response = await api.get("/assets");
        setAllTickers(response.data.data || []);
      } catch (error) {
        console.error("Failed to fetch tickers", error);
      }
    };
    fetchTickers();
  }, []);

  // Fetch Data automatically when Ticker or Time Filter changes
  useEffect(() => {
    const fetchData = async () => {
      if (!selectedTicker || selectedTicker === "Select a ticker") return;

      setIsLoading(true);
      try {
        // Note: You'd ideally pass the timeFilter to your API here
        const response = await api.get(`/assets/price/${selectedTicker}`);
        const data = response.data.data.historicalPrice;

        // Sort data by date to ensure chart renders correctly
        const formattedData = Object.entries(data)
          .map(([date, price]) => ({ date, price }))
          .sort((a, b) => new Date(a.date) - new Date(b.date));

        setStockHistory(formattedData);
      } catch (error) {
        setStockHistory([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [selectedTicker, timeFilter]);

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip">
          <p className="tooltip-date">{new Date(label).toLocaleDateString()}</p>
          <p className="tooltip-price">{formatCurrency(payload[0].value)}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="stock-card">
      {/* Header Section */}
      <div className="stock-header">
        <div>
          <h2 className="chart-title">Market Performance</h2>
          <p className="chart-subtitle">Real-time asset tracking</p>
        </div>

        {/* Controls */}
        <div className="controls-wrapper">
          <div className="ticker-select-wrapper">
            <select
              className="modern-select"
              value={selectedTicker}
              onChange={(e) => setSelectedTicker(e.target.value)}
            >
              <option value="" disabled>
                Select Asset
              </option>
              {tickerOptions}
            </select>
          </div>

          {/* Time Filters */}
          <div className="time-filters">
            {timeFilterOptions.map((filter) => (
              <button
                key={filter}
                className={`filter-btn ${
                  timeFilter === filter ? "active" : ""
                }`}
                onClick={() => setTimeFilter(filter)}
              >
                {filter}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Chart Section */}
      <div className="chart-container">
        {isLoading ? (
          <div className="loading-state">
            <Loader2 className="animate-spin" size={40} color="#00b894" />
          </div>
        ) : stockHistory.length > 0 ? (
          <ResponsiveContainer width="100%" height={350} focus="none">
            <AreaChart
              data={stockHistory}
              margin={{ top: 10, right: 0, left: 0, bottom: 0 }}
              outline="none"
            >
              <defs>
                <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00b894" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#00b894" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid
                strokeDasharray="3 3"
                vertical={false}
                stroke="#2d3436"
              />
              <XAxis
                dataKey="date"
                tickFormatter={formatDate}
                tick={{ fill: "#b2bec3", fontSize: 12 }}
                axisLine={false}
                tickLine={false}
                minTickGap={30}
              />
              <YAxis
                domain={["auto", "auto"]}
                tickFormatter={(number) => `$${number}`}
                tick={{ fill: "#b2bec3", fontSize: 12 }}
                axisLine={false}
                tickLine={false}
                width={60}
              />
              <Tooltip
                content={<CustomTooltip />}
                cursor={{
                  stroke: "#00b894",
                  strokeWidth: 1,
                  strokeDasharray: "5 5",
                }}
              />
              <Area
                type="monotone"
                dataKey="price"
                stroke="#00b894"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorPrice)"
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="empty-state-wrapper">
            <EmptyContent
              message="No Asset Selected"
              subMessage="Select a ticker to view price history"
              icon={<CircleQuestionMark size={64} color="#636e72" />}
            />
          </div>
        )}
      </div>
    </div>
  );
}
