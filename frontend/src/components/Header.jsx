import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Bell, Moon, Sun, Menu, Settings, User, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Header({ onMenuToggle }) {
  const { user, darkMode, toggleDarkMode, logout } = useAuth();
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const notifications = [
    { id: 1, text: 'Document "GST_Return_Q4.pdf" analyzed successfully', time: '2 min ago', unread: true },
    { id: 2, text: 'Compliance alert: 3 documents need attention', time: '1 hour ago', unread: true },
    { id: 3, text: 'New regulatory update available', time: '3 hours ago', unread: false },
  ];

  return (
    <header className="sticky top-0 z-30 bg-white/80 dark:bg-dark-card/80 backdrop-blur-lg border-b border-gray-200 dark:border-dark-border px-6 py-3">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-4 flex-1">
          <button onClick={onMenuToggle} className="lg:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-border">
            <Menu className="w-5 h-5 text-gray-600 dark:text-dark-muted" />
          </button>
          <div className="relative flex-1 max-w-md hidden sm:block">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search documents, entities..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-lg bg-gray-100 dark:bg-dark-bg border-0 text-sm focus:ring-2 focus:ring-primary-500/20 outline-none transition-all"
            />
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button onClick={toggleDarkMode} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-border transition-colors">
            {darkMode ? <Sun className="w-5 h-5 text-saffron-500" /> : <Moon className="w-5 h-5 text-gray-600" />}
          </button>

          <div className="relative">
            <button onClick={() => { setShowNotifications(!showNotifications); setShowUserMenu(false); }} className="relative p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-border transition-colors">
              <Bell className="w-5 h-5 text-gray-600 dark:text-dark-muted" />
              <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-saffron-500 rounded-full border-2 border-white dark:border-dark-card" />
            </button>
            <AnimatePresence>
              {showNotifications && (
                <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 8 }} className="absolute right-0 top-full mt-2 w-80 bg-white dark:bg-dark-card rounded-xl shadow-xl border border-gray-200 dark:border-dark-border overflow-hidden">
                  <div className="px-4 py-3 border-b border-gray-100 dark:border-dark-border">
                    <h3 className="font-semibold text-sm">Notifications</h3>
                  </div>
                  <div className="max-h-64 overflow-y-auto">
                    {notifications.map((n) => (
                      <div key={n.id} className={`px-4 py-3 border-b border-gray-50 dark:border-dark-border last:border-0 hover:bg-gray-50 dark:hover:bg-dark-bg ${n.unread ? 'bg-saffron-50/50 dark:bg-saffron-900/10' : ''}`}>
                        <p className="text-sm text-gray-700 dark:text-dark-text">{n.text}</p>
                        <p className="text-xs text-gray-400 mt-1">{n.time}</p>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <div className="relative">
            <button onClick={() => { setShowUserMenu(!showUserMenu); setShowNotifications(false); }} className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-border transition-colors">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-saffron-500 flex items-center justify-center text-white font-semibold text-sm">
                {user?.name?.charAt(0)?.toUpperCase() || 'U'}
              </div>
            </button>
            <AnimatePresence>
              {showUserMenu && (
                <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 8 }} className="absolute right-0 top-full mt-2 w-56 bg-white dark:bg-dark-card rounded-xl shadow-xl border border-gray-200 dark:border-dark-border overflow-hidden">
                  <div className="px-4 py-3 border-b border-gray-100 dark:border-dark-border">
                    <p className="font-medium text-sm">{user?.name}</p>
                    <p className="text-xs text-gray-500 dark:text-dark-muted">{user?.email}</p>
                  </div>
                  <div className="py-1">
                    <button className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 dark:text-dark-text hover:bg-gray-50 dark:hover:bg-dark-bg"><User className="w-4 h-4" />Profile</button>
                    <button className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 dark:text-dark-text hover:bg-gray-50 dark:hover:bg-dark-bg"><Settings className="w-4 h-4" />Settings</button>
                    <button onClick={logout} className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/10"><LogOut className="w-4 h-4" />Logout</button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </header>
  );
}
