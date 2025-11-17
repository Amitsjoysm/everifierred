import React, { createContext, useState, useContext, useEffect } from 'react';
import { getUser, getToken, setToken, setUser as saveUser, logout as logoutUser } from '../utils/auth';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(getUser());
  const [token, setTokenState] = useState(getToken());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(false);
  }, []);

  const login = (tokenData, userData) => {
    setToken(tokenData);
    saveUser(userData);
    setTokenState(tokenData);
    setUser(userData);
  };

  const logout = () => {
    logoutUser();
    setTokenState(null);
    setUser(null);
  };

  const value = {
    user,
    token,
    loading,
    login,
    logout,
    isAuthenticated: !!token,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
