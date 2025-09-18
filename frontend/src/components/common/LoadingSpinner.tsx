import React from 'react';
import { Spin } from 'antd';

const LoadingSpinner: React.FC = () => {
  return (
    <div style={{ textAlign: 'center', padding: 20 }}>
      <Spin size="large" />
    </div>
  );
};

export default LoadingSpinner;
