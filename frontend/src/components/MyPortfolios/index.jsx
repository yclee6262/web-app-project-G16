import "./index.css";
import PortfolioBar from "./PorfolioBar";
import PortfolioEdit from "./PortfolioEdit";
import { useEffect, useState } from "react";
import Modal from "../Modal";
import api from "../api";
import { useContext } from "react";
import { StoreContext } from "../Utils/Context";
import EmptyContent from "../Utils/EmptyContent";
import { FolderPlus } from "lucide-react";

export default function MyPortfolios() {
  const { userInfo, refreshTrigger } = useContext(StoreContext);

  const [showEditModal, setShowEditModal] = useState(false);
  const [portfolioDatas, setPortfolioDatas] = useState([]);

  const fetchPortfolios = useCallback(async () => {
    if (!userInfo?.userId) return;
    try {
      const response = await api.get(`/portfolio/${userInfo.userId}`);
      setPortfolioDatas(response.data.data);
    } catch (error) {
      console.error("Failed to fetch portfolios", error);
    }
  }, [userInfo]); // Re-create function only if user changes

  useEffect(() => {
    fetchPortfolios();
  }, [fetchPortfolios, refreshTrigger.portfolioRefreshTrigger]);
  return (
    <div className="my-portfolios">
      <header>
        <div>
          <h1>My Portfolio</h1>
          <p className="portfolio-description">
            Construct your portfolio by adding assets below.
          </p>
        </div>
        <button onClick={() => setShowEditModal(true)}>Add Portfolio</button>
      </header>
      {portfolioDatas.map((portfolioData, index) => (
        <PortfolioBar key={index} portfolioData={portfolioData} />
      ))}
      {portfolioDatas.length === 0 && (
        <EmptyContent message="No portfolios yet" icon={<FolderPlus size={200}/>} />
      )}
      {showEditModal && (
        <Modal onClose={() => setShowEditModal(false)}>
          <PortfolioEdit
            portfolioData={{
              name: `My portfolio ${portfolioDatas.length + 1}`,
              assets: [],
            }}
            status={"save"}
            onClose={() => setShowEditModal(false)}
          />
        </Modal>
      )}
    </div>
  );
}
