import storage from 'redux-persist/lib/storage';
import { PersistConfig } from 'redux-persist';
import { RootState } from './rootReducer';

const persistConfig: PersistConfig<RootState> = {
  key: 'root',
  storage,
  whitelist: ['auth'], // only auth slice persisted
};

export default persistConfig;
