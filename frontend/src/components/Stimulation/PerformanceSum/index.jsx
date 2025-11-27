import "./index.css";

export default function PerformanceSum({ stimulatedMetrics }) {
  const percentileOptions = ["10th", "25th", "50th", "75th", "90th"];
  const rows = [
    {
      label: "End Balance",
      key: "end_value",
      format: (v) => `$${v.toLocaleString()}`,
    },
    { label: "Total Return", key: "total_return", format: (v) => `${v}%` },
    {
      label: "Max Drawdown",
      key: "max_drawdown",
      format: (v) => `${(v * 100).toFixed(2)}%`,
    },
    {
      label: "Mean Annual Return",
      key: "annual_return",
      format: (v) => `${(v * 100).toFixed(2)}%`,
    },
    {
      label: "Annual Volatility",
      key: "annual_volatility",
      format: (v) => `${(v * 100).toFixed(2)}%`,
    },
    { label: "Sharpe Ratio", key: "sharpe_ratio" },
  ];
  return (
    <div className="performance-metric-container">
      <h3 style={{ color: "#3378f1" }}>Performance Summary</h3>
      <table className="performance-summary-table">
        <thead>
          <tr>
            <th></th>
            {percentileOptions.map((percentile) => (
              <th key={percentile}>{percentile} percentile</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.key}>
              <td>{row.label}</td>
              {percentileOptions.map((percentile) => (
                <td key={percentile}>
                  {row.format
                    ? row.format(stimulatedMetrics[percentile][row.key])
                    : stimulatedMetrics[percentile][row.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
