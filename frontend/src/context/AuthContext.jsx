import { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';
import toast from 'react-hot-toast';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('docsetu_darkmode');
    return saved ? JSON.parse(saved) : false;
  });

  useEffect(() => {
    const token = localStorage.getItem('docsetu_token');
    const savedUser = localStorage.getItem('docsetu_user');

    if (token && savedUser) {
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    localStorage.setItem('docsetu_darkmode', JSON.stringify(darkMode));
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  const login = async (email, password) => {
    try {
      const response = await authAPI.login({ email, password });
      const { token, user: userData } = response.data;
      localStorage.setItem('docsetu_token', token);
      localStorage.setItem('docsetu_user', JSON.stringify(userData));
      setUser(userData);
      toast.success('Welcome back!');
      return { success: true };
    } catch (error) {
      const message = error.response?.data?.message || 'Login failed';
      toast.error(message);
      return { success: false, message };
    }
  };

  const register = async (name, email, password, organization) => {
    try {
      const response = await authAPI.register({ name, email, password, organization });
      const { token, user: userData } = response.data;
      localStorage.setItem('docsetu_token', token);
      localStorage.setItem('docsetu_user', JSON.stringify(userData));
      setUser(userData);
      toast.success('Account created successfully!');
      return { success: true };
    } catch (error) {
      const message = error.response?.data?.message || 'Registration failed';
      toast.error(message);
      return { success: false, message };
    }
  };

  const logout = () => {
    localStorage.removeItem('docsetu_token');
    localStorage.removeItem('docsetu_user');
    setUser(null);
    toast.success('Logged out successfully');
  };

  const toggleDarkMode = () => {
    setDarkMode((prev) => !prev);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        darkMode,
        login,
        register,
        logout,
        toggleDarkMode,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
