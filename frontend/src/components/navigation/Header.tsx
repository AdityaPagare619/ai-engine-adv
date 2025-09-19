import React from 'react';
import { Link } from 'react-router-dom';

const Header: React.FC = () => {
  return (
    <header style={{ padding: 16, backgroundColor: '#001529', color: '#fff' }}>
      <h1>
        <Link to="/" style={{ color: '#fff', textDecoration: 'none' }}>
          MyApp
        </Link>
      </h1>
    </header>
  );
};

export default Header;
