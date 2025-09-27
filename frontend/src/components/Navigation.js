import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Navigation.css';

function Navigation() {
  const location = useLocation();

  const isActive = (path) => {
    return location.pathname === path ? 'nav-link active' : 'nav-link';
  };

  return (
    <nav className="navigation">
      <div className="nav-container">
        <div className="nav-brand">
          <h1>Legal Simulation System</h1>
        </div>
        <div className="nav-menu">
          <Link to="/dashboard" className={isActive('/dashboard')}>
            Dashboard
          </Link>
          <Link to="/new-case" className={isActive('/new-case')}>
            New Case
          </Link>
        </div>
      </div>
    </nav>
  );
}

export default Navigation;
