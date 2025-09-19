import { Middleware } from 'redux';
import logger from 'redux-logger';
import thunk from 'redux-thunk';

const middleware: Middleware[] = [thunk];

// Add logger only in development
if (process.env.NODE_ENV === 'development') {
  middleware.push(logger);
}

export default middleware;
