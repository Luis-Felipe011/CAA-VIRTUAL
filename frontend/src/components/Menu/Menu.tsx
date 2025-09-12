// Atualizado com base no protótipo visual

// Menu.tsx
import React from 'react';
import './Menu.scss';
import { Link, useLocation } from 'react-router-dom';
import { FaUsers, FaMoneyBill, FaHome } from 'react-icons/fa';

interface MenuProps {
    onSelecionarSecao: (secao: string) => void;
  }
  
  const Menu: React.FC<MenuProps> = ({ onSelecionarSecao }) => {
    return (
      <nav className="menu">
        <ul>
          <li onClick={() => onSelecionarSecao("grupo-familiar")}>
            <a><FaUsers className="icon" /> Grupo Familiar</a>
          </li>
          <li onClick={() => onSelecionarSecao("renda")}>
            <a><FaMoneyBill className="icon" /> Renda</a>
          </li>
          <li onClick={() => onSelecionarSecao("patrimonial")}>
            <a><FaHome className="icon" /> Patrimonial</a>
          </li>
        </ul>
      </nav>
    );
  };
export default Menu;