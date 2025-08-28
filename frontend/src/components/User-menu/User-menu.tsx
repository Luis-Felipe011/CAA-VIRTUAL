import React from 'react';
import './User-menu.scss';

interface UserMenuProps {
  userName: string;
  userEmail: string;
  userImage: string;
  onLogout: () => void;
}

const UserMenu: React.FC<UserMenuProps> = ({ userName, userEmail, userImage, onLogout }) => {
  return (
    <div className="user-menu">
      <div className="user-menu__avatar">
        {userImage ? (
          <img src={userImage} alt={userName} />
        ) : (
          <span>{userName[0]?.toUpperCase() || "U"}</span>
        )}
      </div>
      <div className="user-menu__info">
        <span className="user-menu__name">{userName}</span>
      </div>
      <button
        className="user-menu__logout"
        onClick={() => {
          onLogout();
          window.location.href = "/";
        }}
      >
        Sair
      </button>
    </div>
  );
};

export default UserMenu;