import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown } from 'lucide-react';

export default function StatsCard({ title, value, icon: Icon, trend, trendValue, color = 'primary', index = 0 }) {
  const bgColorMap = {
    primary: 'bg-primary-50 dark:bg-primary-900/20',
    saffron: 'bg-saffron-50 dark:bg-saffron-900/20',
    green: 'bg-green-50 dark:bg-green-900/20',
    red: 'bg-red-50 dark:bg-red-900/20',
    purple: 'bg-purple-50 dark:bg-purple-900/20',
  };

  const iconColorMap = {
    primary: '#000080',
    saffron: '#FF9933',
    green: '#138808',
    red: '#ef4444',
    purple: '#8b5cf6',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className="card hover:shadow-md transition-all duration-300"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-500 dark:text-dark-muted">{title}</p>
          <p className="text-2xl font-bold mt-1 text-gray-900 dark:text-white">{value}</p>
          {trendValue && (
            <div className="flex items-center gap-1 mt-2">
              {trend === 'up' ? (
                <TrendingUp className="w-3.5 h-3.5 text-green-500" />
              ) : (
                <TrendingDown className="w-3.5 h-3.5 text-red-500" />
              )}
              <span className={`text-xs font-medium ${trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>
                {trendValue}
              </span>
              <span className="text-xs text-gray-400 ml-1">vs last month</span>
            </div>
          )}
        </div>
        <div className={`p-3 rounded-xl ${bgColorMap[color]}`}>
          <Icon className="w-6 h-6" style={{ color: iconColorMap[color] }} />
        </div>
      </div>
    </motion.div>
  );
}
