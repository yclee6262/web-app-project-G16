import { useState, useEffect, useContext, useMemo} from "react";
import "./index.css";
import api from "../../api";
import UseNotify from "../../Utils/UseNotify";
import { StoreContext } from "../../Utils/Context";
import { handleResponse, handleError } from "../../Utils/Response";

export default function PortfolioEdit({ portfolioData, status, onClose}) {
  const { userInfo, triggerPortfolioRefresh } = useContext(StoreContext);
  const { name, assets, portfolioId } = portfolioData;
  const notify = UseNotify();

  // State
  const [assetList, setAssetList] = useState(assets || []);
  const [allTickers, setAllTickers] = useState([]);
  const [portfolioName, setPortfolioName] = useState(name || "");
  const [isLoading, setIsLoading] = useState(false); // New: Prevent double submissions

  const tickerOptions = useMemo(() => {
    return allTickers.map((ticker) => (
      <option key={ticker} value={ticker}>
        {ticker}
      </option>
    ));
  }, [allTickers]);

  const handleSharesChange = (index, value) => {
    setAssetList((prevAssets) =>
      prevAssets.map((item, i) =>
        i === index ? { ...item, quantity: value } : item
      )
    );
  };

  const handleClassChange = (indexToChange, newValue) => {
    if (!newValue) return;

    // Check for duplicates
    const isDuplicate = assetList.some(
      (asset, index) => index !== indexToChange && asset.ticker === newValue
    );

    if (isDuplicate) {
      notify("Duplicate asset class selected.", "error");
      return;
    }

    setAssetList((prevAssets) =>
      prevAssets.map((item, i) =>
        i === indexToChange ? { ...item, ticker: newValue } : item
      )
    );
  };

  const removeAsset = (indexToRemove) => {
    setAssetList((prev) => prev.filter((_, i) => i !== indexToRemove));
  };

  const addAsset = () => {
    setAssetList((prev) => [...prev, { ticker: "", quantity: "" }]);
  };

  const getValidAssets = () => {
    return assetList.filter((asset) => asset.ticker && asset.quantity > 0);
  };

  const savePortfolio = async () => {
    const validAssets = getValidAssets();

    if (validAssets.length === 0) {
      notify("Portfolio must have at least one valid asset.", "error");
      return;
    }

    setIsLoading(true); // Start loading

    const payload = {
      name: portfolioName,
      assets: validAssets,
      userId: userInfo.userId,
    };

    try {
      const response = await api.post("/portfolio/create", payload);
      triggerPortfolioRefresh();
      onClose();
      handleResponse(response, "Portfolio saved successfully.", notify);
    } catch (error) {
      handleError(error, "Failed to save portfolio.", notify);
    } finally {
      setIsLoading(false); // End loading
    }
  };

  const updatePortfolio = async () => {
    const validAssets = getValidAssets();

    // 4. Fix: Corrected the check for empty assets logic
    if (validAssets.length === 0) {
      notify("Portfolio must have at least one valid asset.", "error");
      return;
    }

    setIsLoading(true);
    // Transform array to object map: { "AAPL": 10, "TSLA": 5 }
    const assetData = validAssets.reduce((acc, curr) => {
      acc[curr.ticker] = Number(curr.quantity);
      return acc;
    }, {});

    const payload = {
      [portfolioId]: assetData,
    };

    try {
      const response = await api.post(`/portfolio/${portfolioId}`, payload);
      onClose();
      handleResponse(response, null, notify); // Message comes from server in your original code
      triggerPortfolioRefresh();
    } catch (error) {
      handleError(error, "Failed to update portfolio.", notify);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const fetchTickers = async () => {
      try {
        const response = await api.get("/assets");
        setAllTickers(response.data.data || []);
      } catch (error) {
        console.error("Failed to fetch tickers", error);
        setAllTickers([]);
      }
    };
    fetchTickers();
  }, []);

  return (
    <div className="portfolio-edit-container">
      <input
        className="portfolio-name"
        type="text"
        placeholder="Portfolio Name"
        value={portfolioName}
        onChange={(e) => setPortfolioName(e.target.value)}
      />

      {/* Semantic HTML: Changed from raw LI to specific structure or keep as is if styled specifically */}
      <nav className="portfolio-nav">
        <ul>
          <li>Portfolio Assets</li>
        </ul>
      </nav>

      <table className="portfolio-edit-table">
        <thead>
          <tr>
            <th>Asset Class</th>
            <th>Shares</th>
          </tr>
        </thead>
        <tbody className="portfolio-edit-body">
          {assetList.map((asset, index) => (
            <tr key={index}>
              <th>
                <select
                  value={asset.ticker || ""}
                  onChange={(e) => handleClassChange(index, e.target.value)}
                >
                  <option value="" disabled>
                    Select Asset Class...
                  </option>
                  {tickerOptions}
                </select>
              </th>
              <td className="allocation-cell">
                <div className="allocation-wrapper">
                  <div className="allocation-input-group">
                    <input
                      type="number"
                      min="0" // UX: Prevent negative numbers in UI
                      value={asset.quantity}
                      onChange={(e) =>
                        handleSharesChange(index, e.target.value)
                      }
                    />
                  </div>
                  <button
                    className="remove-btn"
                    onClick={() => removeAsset(index)}
                    tabIndex="-1" // UX: Prevent tabbing to delete button accidentally
                  >
                    Remove
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div
        className="portfolio-actions"
        style={{
          display: "flex",
          justifyContent: "space-between",
          marginTop: "16px",
        }}
      >
        <button
          className="save-btn"
          onClick={status === "edit" ? updatePortfolio : savePortfolio}
          disabled={isLoading} // UX: Disable while loading
        >
          {isLoading ? "Saving..." : "Save"}
        </button>
        <button className="add-btn" onClick={addAsset}>
          + Add Asset
        </button>
      </div>
    </div>
  );
}
