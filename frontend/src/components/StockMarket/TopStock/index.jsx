import { useEffect, useRef, useState } from "react";
import "./index.css";
import StockInfo from "./StockInfo";

export default function TopStock() {
  // based on the width, this array can be extended to avoid empty spaces during scrolling
  const originalStocks = [
    { ticker: "AAPL", price: 150, change: 1.2 },
    { ticker: "MSFT", price: 280, change: 0.5 },
    { ticker: "AMZN", price: 3400, change: 2.1 },
  ];
  const minSize = 4;
  const scrollingRef = useRef(null);
  const [scrollingContent, setScrollingContent] = useState([]);
  useEffect(() => {
    let content = [...originalStocks];
    while (content.length < minSize) {
      const randomIndex = Math.floor(Math.random() * originalStocks.length);
      content.push(originalStocks[randomIndex]);
    }

    content = [...content, ...content];
    setScrollingContent(content);

    const track = scrollingRef.current;
    if (track) {
      const firstHalfWidth = Array.from(track.children)
        .slice(0, content.length / 2)
        .reduce((sum, el) => sum + el.offsetWidth, 0);

      track.style.setProperty("--scroll-width", `${firstHalfWidth}px`);
    }
  }, []);
  return (
    <div className="ticker-wrapper">
      <ul className="ticker-track">
        {scrollingContent.map((stock, index) => (
          <li key={`${stock.ticker}-${index}`} className="ticker-item">
            <StockInfo stock={stock} />
          </li>
        ))}
      </ul>
    </div>
  );
}
