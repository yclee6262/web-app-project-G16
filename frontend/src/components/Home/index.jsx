import HomeHeader from "./Header";
import NavBar from "./NavBar";
import { useState } from "react";
import Modal from "../Modal";
import Login from "../Login";
import "./index.css";
import { Routes, Route } from "react-router-dom";
import AboutUs from "./Overveiw";
import StockMarket from "../StockMarket";
import MyPortfolios from "../MyPortfolios";
import Stimulation from "../Stimulation";
import PremiumLabel from "./PremiumFeature";
import FloatingAd from "./FloatingAd";
import Watchlist from "./WatchList";

export default function Home() {
  const [showLoginModal, setShowLoginModal] = useState(false);
  const openLoginModal = () => setShowLoginModal(true);
  const closeLoginModal = () => setShowLoginModal(false);

  return (
    <div className="home-container">
      <HomeHeader toggleLoginModal={openLoginModal} />
      <Watchlist />
      <PremiumLabel />
      <FloatingAd />
      <main className="home-main">
        <NavBar />
        <Routes>
          <Route path="/" element={<AboutUs />} />
          <Route path="/stock-market" element={<StockMarket />} />
          <Route path="/portfolio" element={<MyPortfolios />} />
          <Route path="/stimulation" element={<Stimulation />} />
        </Routes>
        {showLoginModal && (
          <Modal onClose={closeLoginModal}>
            <Login onClose={closeLoginModal} />
          </Modal>
        )}
      </main>
    </div>
  );
}
