import React from "react";
import { FaCheckCircle, FaExclamationCircle, FaInfoCircle, FaTimes } from "react-icons/fa";
import "./Toast.scss";

interface ToastProps {
  message: string;
  show: boolean;
  type?: "success" | "error" | "info" | "warning";
  onClose: () => void;
}

const Toast: React.FC<ToastProps> = ({ message, show, type = "info", onClose }) => {
  if (!show) return null;

  // Seleciona o ícone baseado no tipo
  const getIcon = () => {
    switch (type) {
      case "success": return <FaCheckCircle />;
      case "error": return <FaExclamationCircle />;
      case "warning": return <FaExclamationCircle />;
      default: return <FaInfoCircle />;
    }
  };

  return (
    <div className="toast-container">
      <div className={`toast toast-${type}`}> 
        <div className="toast-icon">
          {getIcon()}
        </div>
        <div className="toast-content">
          {message}
        </div>
        <button className="toast-close" onClick={onClose}>
          <FaTimes />
        </button>
      </div>
    </div>
  );
};

export default Toast;