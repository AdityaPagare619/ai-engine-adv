import { useAppSelector, useAppDispatch } from '../features/auth/hooks';
import { login, logout } from '../features/auth/authSlice';

export const useAuth = () => {
  const dispatch = useAppDispatch();
  const authState = useAppSelector(state => state.auth);

  const loginUser = (credentials: { username: string; password: string }) => {
    return dispatch(login(credentials));
  };

  const logoutUser = () => {
    dispatch(logout());
  };

  return {
    ...authState,
    loginUser,
    logoutUser,
  };
};
