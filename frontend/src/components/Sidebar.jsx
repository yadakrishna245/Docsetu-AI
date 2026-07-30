import { NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  Upload,
  FileText,
  Shield,
  BarChart3,
  LogOut,
  X,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/upload', icon: Upload, label: 'Upload' },
  { path: '/documents', icon: FileText, label: 'Documents' },
  { path: '/compliance', icon: Shield, label: 'Compliance' },
  { path: '/analytics', icon: BarChart3, label: 'Analytics' },
];

export default function Sidebar({ isOpen, onClose }) {
  const { user, logout } = useAuth();

  return (
    <>
      {isOpen && (
        <div className="fixed inset-0 bg-black/50 z-40 lg:hidden" onClick={onClose} />
      )}
      <motion.aside
        initial={false}
        animate={{ x: isOpen ? 0 : -280 }}
        className="fixed top-0 left-0 z-50 h-full w-[280px] bg-white dark:bg-dark-card border-r border-gray-200 dark:border-dark-border flex flex-col lg:translate-x-0 lg:static lg:z-auto transition-transform duration-300"
      >
        <div className="flex items-center justify-between px-6 py-5 border-b border-gray-100 dark:border-dark-border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-saffron-500 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-display font-bold text-lg text-gray-900 dark:text-white">DocSetu</h1>
              <span className="text-xs text-saffron-500 font-medium">AI Platform</span>
            </div>
          </div>
          <button onClick={onClose} className="lg:hidden p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-border">
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto scrollbar-thin">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              onClick={onClose}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-primary-500 text-white shadow-lg shadow-primary-500/25'
                    : 'text-gray-600 dark:text-dark-muted hover:bg-gray-100 dark:hover:bg-dark-border hover:text-gray-900 dark:hover:text-white'
                }`
              }
            >
              <item.icon className="w-5 h-5" />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-gray-100 dark:border-dark-border px-4 py-4">
          <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-gray-50 dark:bg-dark-bg">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-saffron-400 to-saffron-600 flex items-center justify-center text-white font-semibold text-sm">
              {user?.name?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{user?.name || 'User'}</p>
              <p className="text-xs text-gray-500 dark:text-dark-muted truncate">{user?.email || 'user@docsetu.ai'}</p>
            </div>
            <button onClick={logout} className="p-1.5 rounded-lg hover:bg-gray-200 dark:hover:bg-dark-border text-gray-500 hover:text-red-500 transition-colors" title="Logout">
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </motion.aside>
    </>
  );
}
