import "./index.css";
import { useState, useContext } from "react";
import { StoreContext } from "../../Utils/Context";

export default function FloatingAd() {
  const [isVisible, setIsVisible] = useState(true);
  const { userInfo, setUserInfo } = useContext(StoreContext);

  const handleClose = () => {
    setIsVisible(false);
    setTimeout(() => {
      setIsVisible(true);
    }, 3000);
  };

  if (!isVisible || userInfo.loginStatus) return null;

  return (
    <div className="floating-ad">
      <button className="close-ad-btn" onClick={handleClose}>
        X
      </button>

      <h3>Test Advertisement</h3>
      <p style={{ textAlign: "center", padding: "0" }}>
        NTU webapp course is very interesting! We got wonderful instructor and
        TA!
      </p>
    </div>
  );
}
