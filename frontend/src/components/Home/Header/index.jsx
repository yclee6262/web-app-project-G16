import "./index.css";
import { useContext } from "react";
import { useNavigate } from "react-router-dom";
import { StoreContext } from "../../Utils/Context";

export default function HomeHeader({ toggleLoginModal }) {
  const navigate = useNavigate();
  const { userInfo, setUserInfo } = useContext(StoreContext);
  const logout = () => {
    setUserInfo({ loginStatus: false, userId: null, userName: "" });
    navigate("/");
  };
  return (
    <header className="home-header">
      <h1 style={{ padding: "15px" }}>NTU Investment</h1>
      <div
        style={{
          padding: "15px",
          display: userInfo.loginStatus ? "block" : "none",
          fontWeight: "bold",
        }}
      >
        Welcome, {userInfo.userName}
      </div>
      <button
        className={`header-login-btn ${userInfo.loginStatus ? "logout" : ""}`}
        onClick={!userInfo.loginStatus ? toggleLoginModal : logout}
      >
        {userInfo.loginStatus ? "Log Out" : "Log In"}
      </button>
    </header>
  );
}
