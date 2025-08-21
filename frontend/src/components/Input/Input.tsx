import React from "react";
import "./Input.scss";

interface InputProps {
  label?: string;
  placeholder?: string;
  value: string;
  onChange: (valor: string) => void;
  type?: string;
  name?: string;
  className?: string; // Permite passar classes personalizadas
}

export default function Input({
  label,
  placeholder,
  value,
  onChange,
  type = "text",
  name,
  className, // Recebe a classe personalizada
}: InputProps) {
  return (
    <div className="input-group">
      {label && <label className="input-label">{label}</label>}
      <input
        type={type}
        name={name}
        placeholder={placeholder}
        className={`input-field ${className}`} // Adiciona a classe personalizada
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}