import React, { createContext, useContext, useState, ReactNode, useCallback } from "react";
import Toast from "../components/Toast/Toast";

interface ToastContextType {
  showToast: (message: string, type?: "success" | "error" | "info") => void;
}

const ToastContext = createContext<ToastContextType>({ showToast: () => {} });

export const useToast = () => useContext(ToastContext);

export const ToastProvider = ({ children }: { children: ReactNode }) => {
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" | "info"; show: boolean }>({
    message: "",
    type: "info",
    show: false,
  });

  const showToast = useCallback((message: string, type: "success" | "error" | "info" = "info") => {
    setToast({ message, type, show: true });
    setTimeout(() => setToast((t) => ({ ...t, show: false })), 3500);
  }, []);

  const handleClose = () => setToast((t) => ({ ...t, show: false }));

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <Toast message={toast.message} show={toast.show} type={toast.type} onClose={handleClose} />
    </ToastContext.Provider>
  );
};
