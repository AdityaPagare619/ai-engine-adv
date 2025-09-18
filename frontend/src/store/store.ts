import { configureStore } from '@reduxjs/toolkit';
import { combineReducers } from 'redux';
import { persistStore, persistReducer } from 'redux-persist';
import storage from 'redux-persist/lib/storage';
import thunk from 'redux-thunk';
import authReducer from '../features/auth/authSlice';
import questionsReducer from '../features/questions/questionSlice';

// Root reducer
const rootReducer = combineReducers({
  auth: authReducer,
  questions: questionsReducer,
  // additional feature reducers will go here
});

// Persist configuration
const persistConfig = {
  key: 'root',
  storage,
  whitelist: ['auth'], // persist auth only
};

// Create persisted reducer
const persistedReducer = persistReducer(persistConfig, rootReducer);

// Configure store
const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false, // avoid redux-persist warnings
    }).concat(thunk),
  devTools: process.env.NODE_ENV !== 'production',
});

// Persistor for persisting store
export const persistor = persistStore(store);

// Infer types
export type RootState = ReturnType<typeof rootReducer>;
export type AppDispatch = typeof store.dispatch;

export default store;
