import "./index.css";
import { useState, useContext } from "react";
import PortfolioEdit from "../PortfolioEdit";
import PortfolioAllocationPieChart from "../PortfolioAllocationPieChart";
import Modal from "../../Modal";
import { StoreContext } from "../../Utils/Context";
import { handleResponse, handleError } from "../../Utils/Response";
import api from "../../api";
import UseNotify from "../../Utils/UseNotify";

const formatCurrency = (value) => {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
};

export default function PortfolioBar({ portfolioData }) {
  return (
    <div className="portfolio-container">
      <PortfolioTable portfolioData={portfolioData} />
      <div className="chart-section">
        <h5 className="section-label">Allocation</h5>
        <PortfolioAllocationPieChart data={portfolioData.assets} />
      </div>
    </div>
  );
}

function PortfolioTable({ portfolioData }) {
  const assets = portfolioData.assets;
  const [showEditModal, setShowEditModal] = useState(false);
  const { triggerPortfolioRefresh } = useContext(StoreContext);
  const notify = UseNotify();

  // Calculate total value for a summary header (Modern touch)
  const totalValue = assets.reduce(
    (acc, curr) => acc + curr.price * curr.quantity,
    0
  );

  const deletePortfolio = async () => {
    try {
      const response = await api.delete(`/portfolio/${portfolioData.portfolioId}`);
      triggerPortfolioRefresh();
      handleResponse(response, "Portfolio deleted successfully.", notify);
    } catch (error) {
      handleError(error, "Failed to delete portfolio.", notify);
    }
  };

  return (
    <div className="table-section">
      <header className="portfolio-header">
        <div>
          <h3 className="portfolio-title">{portfolioData.name}</h3>
          <span className="portfolio-subtitle">
            Total Value: {formatCurrency(totalValue)}
          </span>
        </div>
        <button className="btn-primary" style={{backgroundColor:'red'}} onClick={deletePortfolio}>
          Delete
        </button>
        <button className="btn-primary" onClick={() => setShowEditModal(true)}>
          Edit
        </button>
      </header>

      <div className="table-wrapper">
        <table className="modern-table">
          <thead>
            <tr>
              <th className="text-left">Ticker</th>
              <th className="text-right">Price</th>
              <th className="text-right">Shares</th>
              <th className="text-right">Total</th>
            </tr>
          </thead>
          <tbody>
            {assets.map((asset, index) => (
              <tr key={index}>
                <td className="fw-bold">{asset.ticker}</td>
                <td className="text-right">{formatCurrency(asset.price)}</td>
                <td className="text-right">
                  {asset.quantity.toLocaleString()}
                </td>
                <td className="text-right fw-bold">
                  {formatCurrency(asset.price * asset.quantity)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showEditModal && (
        <Modal onClose={() => setShowEditModal(false)}>
          <PortfolioEdit
            portfolioData={portfolioData}
            status={"edit"}
            onClose={() => setShowEditModal(false)}
          />
        </Modal>
      )}
    </div>
  );
}
