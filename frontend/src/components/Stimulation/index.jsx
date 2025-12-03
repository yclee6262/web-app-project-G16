import "./index.css";
import PerformanceSum from "./PerformanceSum";
import PortfolioBalance from "./PerforlioBalance";
import { useEffect, useContext, useState, useCallback, useRef } from "react";
import { StoreContext } from "../Utils/Context";
import api from "../api";
import EmptyContent from "../Utils/EmptyContent";
import { CircleQuestionMark } from "lucide-react";

export default function Stimulation() {
  const { userInfo, refreshTrigger } = useContext(StoreContext);
  const [portfolioData, setPortfolioData] = useState([]);
  const [stimulatedResults, setStimulatedResults] = useState({});
  const [stimulatedMetrics, setStimulatedMetrics] = useState({});
  const portfolioNamesMpId = useRef({});

  const fetchStimulatedResults = async (portfolio) => {
    if (!portfolio) return;
    const portfolioId = portfolioNamesMpId.current[portfolio];
    if (!portfolioId) return;
    try {
      const response = await api.get(`/portfolio/simulation/${portfolioId}`);
      const data = response.data.data.portfolioVal;
      const updatedMetrics = {};
      const updatedResults = {};
      data.forEach((item) => {
        const { values, ...rest } = item;
        updatedResults[rest.percentile] = values;
        updatedMetrics[rest.percentile] = rest;
      });
      setStimulatedMetrics(updatedMetrics);
      setStimulatedResults(updatedResults);
    } catch (error) {
      console.error("Failed to fetch stimulated results", error);
    }
  };

  const fetchPortfolioData = useCallback(async () => {
    if (!userInfo?.userId) return;
    try {
      const response = await api.get(`/portfolio/${userInfo.userId}`);
      const ids = response.data.data.map((portfolio) => ({
        portfolioId: portfolio.portfolioId,
        name: portfolio.name,
      }));
      ids.forEach(({ portfolioId, name }) => {
        portfolioNamesMpId.current[name] = portfolioId;
      });
      setPortfolioData(ids);
    } catch (error) {
      console.error("Failed to fetch portfolios", error);
    }
  }, [userInfo]);

  useEffect(() => {
    fetchPortfolioData();
  }, [fetchPortfolioData, refreshTrigger.portfolioRefreshTrigger]);

  return (
    <div className="stimulation-container">
      <header>
        <div>
          <h1>Monte Carlo Simulation</h1>
          <p className="stimulation-description">
            Monte carlo simulation for portfolio
          </p>
        </div>
        <select
          name="portfolio"
          id="portfolio"
          onChange={(e) => {
            fetchStimulatedResults(e.target.value);
          }}
        >
          <option value="">-- Select Portfolio --</option>
          {portfolioData.map((portfolio) => (
            <option key={portfolio.portfolioId} value={portfolio.name}>
              {portfolio.name}
            </option>
          ))}
        </select>
      </header>
      {Object.keys(stimulatedResults).length > 0 ? (
        <main className="stimulation-main">
          <PerformanceSum stimulatedMetrics={stimulatedMetrics} />
          <PortfolioBalance stimulatedResults={stimulatedResults} />
        </main>
      ) : (
        <EmptyContent
          icon={<CircleQuestionMark size={64} color="white" />}
          message={"No simulation results available."}
          subMessage={"Please select a portfolio to view simulation results."}
        />
      )}
    </div>
  );
}
