import { combineReducers } from 'redux';
import authReducer from '../features/auth/authSlice';
import questionsReducer from '../features/questions/questionSlice';

const rootReducer = combineReducers({
  auth: authReducer,
  questions: questionsReducer,
  // future reducers go here
});

export type RootState = ReturnType<typeof rootReducer>;
export default rootReducer;
