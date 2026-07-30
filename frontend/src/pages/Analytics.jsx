import { motion } from 'framer-motion';
import { TrendingUp, FileText, Shield, AlertTriangle } from 'lucide-react';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';

const docsOverTime = [
  { month: 'Jan', docs: 120 },
  { month: 'Feb', docs: 180 },
  { month: 'Mar', docs: 250 },
  { month: 'Apr', docs: 310 },
  { month: 'May', docs: 380 },
  { month: 'Jun', docs: 420 },
  { month: 'Jul', docs: 520 },
];

const docTypes = [
  { name: 'GST Returns', value: 35, color: '#000080' },
  { name: 'Invoices', value: 25, color: '#FF9933' },
  { name: 'PAN/Aadhaar', value: 20, color: '#138808' },
  { name: 'Bank Statements', value: 12, color: '#8b5cf6' },
  { name: 'Others', value: 8, color: '#6b7280' },
];

const complianceTrend = [
  { month: 'Jan', compliant: 65, partial: 20, nonCompliant: 15 },
  { month: 'Feb', compliant: 68, partial: 18, nonCompliant: 14 },
  { month: 'Mar', compliant: 72, partial: 17, nonCompliant: 11 },
  { month: 'Apr', compliant: 74, partial: 16, nonCompliant: 10 },
  { month: 'May', compliant: 76, partial: 15, nonCompliant: 9 },
  { month: 'Jun', compliant: 75, partial: 16, nonCompliant: 9 },
  { month: 'Jul', compliant: 78, partial: 15, nonCompliant: 7 },
];

const topIssues = [
  { issue: 'Missing HSN Code in invoices', count: 23, severity: 'high' },
  { issue: 'Expired KYC documents', count: 18, severity: 'high' },
  { issue: 'GST mismatch between invoice and return', count: 15, severity: 'medium' },
  { issue: 'Digital signature expired', count: 12, severity: 'medium' },
  { issue: 'Incomplete address fields', count: 8, severity: 'low' },
];

export default function Analytics() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-display font-bold text-gray-900 dark:text-white">Analytics</h1>
        <p className="text-sm text-gray-500 dark:text-dark-muted mt-1">Document processing insights and compliance trends.</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        {[
          { label: 'This Month', value: '520', icon: FileText, change: '+23%' },
          { label: 'Avg. Processing', value: '4.2s', icon: TrendingUp, change: '-15%' },
          { label: 'Compliance Rate', value: '78%', icon: Shield, change: '+3%' },
          { label: 'Issues Found', value: '76', icon: AlertTriangle, change: '-12%' },
        ].map((item, i) => (
          <motion.div key={i} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }} className="card">
            <div className="flex items-center gap-3">
              <item.icon className="w-5 h-5 text-primary-500" />
              <div>
                <p className="text-xs text-gray-500 dark:text-dark-muted">{item.label}</p>
                <p className="text-xl font-bold">{item.value}</p>
              </div>
              <span className="ml-auto text-xs font-medium text-green-600 bg-green-50 dark:bg-green-900/20 px-2 py-0.5 rounded">{item.change}</span>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Documents Over Time */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="card">
          <h2 className="text-lg font-semibold mb-4">Documents Processed</h2>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={docsOverTime}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Line type="monotone" dataKey="docs" stroke="#FF9933" strokeWidth={3} dot={{ fill: '#FF9933', r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Document Types */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="card">
          <h2 className="text-lg font-semibold mb-4">Document Types</h2>
          <div className="flex items-center">
            <ResponsiveContainer width="60%" height={250}>
              <PieChart>
                <Pie data={docTypes} cx="50%" cy="50%" outerRadius={90} dataKey="value" strokeWidth={0}>
                  {docTypes.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="space-y-2">
              {docTypes.map((type) => (
                <div key={type.name} className="flex items-center gap-2 text-sm">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: type.color }} />
                  <span className="text-gray-600 dark:text-dark-muted">{type.name}</span>
                  <span className="font-medium ml-auto">{type.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Compliance Trend */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }} className="card">
          <h2 className="text-lg font-semibold mb-4">Compliance Trend</h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={complianceTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="compliant" fill="#138808" radius={[2, 2, 0, 0]} />
              <Bar dataKey="partial" fill="#FF9933" radius={[2, 2, 0, 0]} />
              <Bar dataKey="nonCompliant" fill="#ef4444" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Top Issues */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }} className="card">
          <h2 className="text-lg font-semibold mb-4">Top Issues Found</h2>
          <div className="space-y-3">
            {topIssues.map((issue, i) => (
              <div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 dark:bg-dark-bg">
                <span className="text-lg font-bold text-gray-300 w-6">#{i + 1}</span>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">{issue.issue}</p>
                  <span className={`text-xs font-medium ${
                    issue.severity === 'high' ? 'text-red-600' :
                    issue.severity === 'medium' ? 'text-yellow-600' : 'text-blue-600'
                  }`}>{issue.severity} severity</span>
                </div>
                <span className="text-sm font-semibold text-gray-500">{issue.count}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
