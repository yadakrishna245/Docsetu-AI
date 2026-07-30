import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import Documents from './pages/Documents';
import DocumentDetail from './pages/DocumentDetail';
import Compliance from './pages/Compliance';
import Analytics from './pages/Analytics';
import Login from './pages/Login';
import Register from './pages/Register';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-dark-bg">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-saffron-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-500 dark:text-dark-muted">Loading DocSetu AI...</p>
        </div>
      </div>
    );
  }

  return user ? children : <Navigate to="/login" replace />;
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="upload" element={<Upload />} />
        <Route path="documents" element={<Documents />} />
        <Route path="documents/:id" element={<DocumentDetail />} />
        <Route path="compliance" element={<Compliance />} />
        <Route path="analytics" element={<Analytics />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
