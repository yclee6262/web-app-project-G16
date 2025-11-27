import {
  LineChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Line,
  ResponsiveContainer,
  ReferenceArea,
} from "recharts";
import "./index.css";
import { useMemo, useState } from "react";

export default function PortfolioBalance({ stimulatedResults }) {
  // 1. State for the current zoom range
  const percentiles = ["10th", "25th", "50th", "75th", "90th"];
  const colors = ["#8884d8", "#82ca9d", "#ffc658", "#ff7300", "#387908"];
  // 2. State for the "selection box" while dragging
  const [refAreaLeft, setRefAreaLeft] = useState("");
  const [refAreaRight, setRefAreaRight] = useState("");
  const [yBound, setYBound] = useState(["auto", "auto"]);
  const [xBound, setXBound] = useState(["dataMin", "dataMax"]);
  ``;
  const formatYAxis = (tick) => {
    if (tick >= 1000000) return `$${(tick / 1000000).toFixed(1)}M`;
    if (tick >= 1000) return `$${(tick / 1000).toFixed(1)}K`;
    return `$${tick.toFixed(2)}`;
  };

  const data = useMemo(() => {
    const generatedData = [];
    // Assuming stimulatedResults is not empty and all arrays have the same length
    const dataLength = stimulatedResults[percentiles[0]].length;

    for (let i = 1; i < dataLength; i++) {
      let item = { year: i };
      for (const percentile of percentiles) {
        item[percentile] = stimulatedResults[percentile][i];
      }
      generatedData.push(item);
    }
    return generatedData;
  }, [stimulatedResults, percentiles]);

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div
          style={{
            backgroundColor: "#1f2937", // Dark modern bg
            border: "1px solid #374151",
            borderRadius: "8px",
            padding: "12px",
            boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
            minWidth: "150px",
          }}
        >
          <p
            style={{ color: "#9ca3af", marginBottom: "8px", fontSize: "12px" }}
          >
            Year: {label}
          </p>
          {payload.map((entry, index) => (
            <div
              key={index}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                marginBottom: "4px",
              }}
            >
              <div
                style={{
                  width: "8px",
                  height: "8px",
                  borderRadius: "50%",
                  backgroundColor: entry.color,
                }}
              />
              <span
                style={{ color: "#f3f4f6", fontSize: "14px", fontWeight: 500 }}
              >
                {entry.name}:
              </span>
              <span
                style={{
                  color: "#f3f4f6",
                  marginLeft: "auto",
                  fontWeight: "bold",
                }}
              >
                {formatYAxis(entry.value)}
              </span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  const zoomOut = () => {
    setLeft("dataMin");
    setRight("dataMax");
    setYBound(["auto", "auto"]);
    setRefAreaLeft("");
    setRefAreaRight("");
  };

  // 4. Helper: Perform the Zoom on Mouse Up
  const zoom = () => {
    if (refAreaLeft === refAreaRight || refAreaRight === "") {
      setRefAreaLeft("");
      setRefAreaRight("");
      return;
    }

    let newLeft = refAreaLeft;
    let newRight = refAreaRight;

    if (newLeft > newRight) {
      [newLeft, newRight] = [newRight, newLeft];
    }
    const visibleData = data.filter(
      (d) => d.year >= newLeft && d.year <= newRight
    );

    if (visibleData.length === 0) {
      setRefAreaLeft("");
      setRefAreaRight("");
      return;
    }

    const allValuesInWindow = visibleData.flatMap((item) =>
      percentiles.map((key) => item[key])
    );

    const dataMin = Math.min(...allValuesInWindow);
    const dataMax = Math.max(...allValuesInWindow);

    const padding = (dataMax - dataMin) * 0.05;
    setRefAreaLeft("");
    setRefAreaRight("");
    setXBound([newLeft, newRight]);
    setYBound([dataMin - padding, dataMax + padding]);
  };
  return (
    <div className="portfolio-balance-container">
      {/* Header with Reset Button */}
      <header className="portfolio-balance-header">
        <h3 style={{ color: "#3378f1", marginBottom: "20px" }}>
          Performance Balance
        </h3>
        <button
          className="reset-btn"
          onClick={zoomOut}
          disabled={xBound[0] === "dataMin" && xBound[1] === "dataMax"} // Disable if already zoomed out
          style={{
            cursor: xBound[0] === "dataMin" ? "default" : "pointer",
            opacity: xBound[0] === "dataMin" ? 0.5 : 1,
            backgroundColor: xBound[0] === "dataMin" ? "#374151" : "#3b82f6", // Gray if disabled, Blue if active
          }}
        >
          Reset Zoom
        </button>
      </header>
      <ResponsiveContainer width="100%" height={450}>
        <LineChart
          data={data}
          margin={{ top: 20, right: 20, left: 0, bottom: 20 }}
          onMouseDown={(e) => e && setRefAreaLeft(e.activeLabel)}
          onMouseMove={(e) =>
            refAreaLeft && e && setRefAreaRight(e.activeLabel)
          }
          onMouseUp={zoom}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            vertical={false}
            stroke="#374151"
            opacity={0.4}
          />
          <XAxis
            allowDataOverflow
            type="number"
            dataKey="year"
            axisLine={false}
            tickLine={false}
            domain={xBound}
            tick={{ fill: "#9ca3af", fontSize: 12 }}
            dy={10} // Push text down slightly
          />
          <YAxis
            allowDataOverflow
            width={80}
            type="number"
            domain={yBound}
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#9ca3af", fontSize: 12 }}
            tickFormatter={formatYAxis}
          />
          <Tooltip
            content={<CustomTooltip />}
            cursor={{
              stroke: "#4b5563",
              strokeWidth: 1,
              strokeDasharray: "4 4",
            }}
          />

          <Legend verticalAlign="top" height={36} iconType="circle" />

          {percentiles.map((percentile, index) => (
            <Line
              key={percentile}
              type="natural" // or "natural" for smoother curves
              dataKey={percentile}
              stroke={colors[index]}
              strokeWidth={2} // Make the line prominent
              dot={false}
              activeDot={{ r: 6, strokeWidth: 0, fill: colors[index] }} // Only show dot on hover
              animationDuration={1500}
            />
          ))}
          {refAreaLeft && refAreaRight ? (
            <ReferenceArea
              x1={refAreaLeft}
              x2={refAreaRight}
              strokeOpacity={1}
              backgroundColor="transparent"
              border="1px solid #fff"
              opacity={0.2}
            />
          ) : null}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
