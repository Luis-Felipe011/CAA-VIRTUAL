import React from 'react';
import './Button.scss';

interface ButtonProps {
  text: string;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
  className?: string;
  color?: 'primary' | 'secondary' | 'danger' | 'outline';
  size?: 'small' | 'medium' | 'large';
}

const Button: React.FC<ButtonProps> = ({ text, onClick, type = 'button', className = '', color = 'primary', size = 'medium' }) => {
  return (
    <button type={type} className={`button ${color} ${size} ${className}`} onClick={onClick}>
      {text}
    </button>
  );
};

export default Button;