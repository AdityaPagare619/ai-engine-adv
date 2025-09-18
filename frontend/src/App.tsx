import React from 'react';
import TestPage from './components/dashboard/TestPage';
import './styles/global.css';

function App() {
  return (
    <div className="App">
      <TestPage />
    </div>
  );
}

export default App;

import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { Provider } from 'react-redux';
import { ConfigProvider } from 'antd';
import AppRoutes from './routes/AppRoutes';
import store from './store/store';
import 'antd/dist/reset.css';
import './styles/globals.css';

const App: React.FC = () => (
  <Provider store={store}>
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#1890ff',
          borderRadius: 4,
        },
      }}
    >
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </ConfigProvider>
  </Provider>
);

export default App;
