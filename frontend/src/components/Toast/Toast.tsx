import React from "react";
import "./Toast.scss";

interface ToastProps {
  message: string;
  show: boolean;
  type?: "success" | "error" | "info";
  onClose: () => void;
}

const Toast: React.FC<ToastProps> = ({ message, show, type = "info", onClose }) => {
  if (!show) return null;
  return (
    <div className={`toast toast-${type}`}> 
      <span>{message}</span>
      <button className="toast-close" onClick={onClose}>
        ×
      </button>
    </div>
  );
};

export default Toast;
