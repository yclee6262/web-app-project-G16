import "./index.css";

export default function EmptyContent({ message, icon, subMessage }) {
  return (
    <div className="empty-state-container">
      {icon}
      <h3 className="empty-state-title">{message}</h3>
      <p className="empty-state-description">{subMessage}</p>
    </div>
  );
}
