import React from 'react';
import './Badge.scss';

interface BadgeProps {
    text: string;
    color?: "success" | "danger" | "info" | "warning" ;
}

const Badge: React.FC<BadgeProps> = ({ text, color = 'success' }) => {
    return (
        <span className={`badge badge-${color}`}>
            {text}
        </span>
    );
};


export default Badge;