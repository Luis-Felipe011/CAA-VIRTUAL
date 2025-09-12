import React from "react";
import "./MainCard.scss";

interface MainCardProps {
  children: React.ReactNode;
}

const MainCard: React.FC<MainCardProps> = ({ children }) => (
  <div className="main-card">
    {children}
  </div>
);

export default MainCard;