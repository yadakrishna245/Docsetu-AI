import { motion } from 'framer-motion';
import { FileText, CheckCircle, AlertTriangle, MessageSquare, Upload, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import StatsCard from '../components/StatsCard';
import ComplianceBadge from '../components/ComplianceBadge';

const stats = [
  { title: 'Total Documents', value: '1,247', icon: FileText, trend: 'up', trendValue: '+12%', color: 'primary' },
  { title: 'Analyzed', value: '1,180', icon: CheckCircle, trend: 'up', trendValue: '+8%', color: 'green' },
  { title: 'Compliance Issues', value: '23', icon: AlertTriangle, trend: 'down', trendValue: '-5%', color: 'saffron' },
  { title: 'AI Queries', value: '3,456', icon: MessageSquare, trend: 'up', trendValue: '+24%', color: 'purple' },
];

const recentDocs = [
  { id: 1, name: 'GST_Return_Q4_2025.pdf', type: 'GST Certificate', status: 'compliant', time: '2 min ago' },
  { id: 2, name: 'PAN_Verification_Sharma.pdf', type: 'PAN Card', status: 'compliant', time: '15 min ago' },
  { id: 3, name: 'Invoice_Tata_Motors.pdf', type: 'Invoice', status: 'partial', time: '1 hour ago' },
  { id: 4, name: 'Bank_Statement_SBI.pdf', type: 'Bank Statement', status: 'non_compliant', time: '2 hours ago' },
  { id: 5, name: 'ITR_2024_25.pdf', type: 'Income Tax Return', status: 'pending', time: '3 hours ago' },
];

const complianceData = [
  { name: 'Compliant', value: 78, color: '#138808' },
  { name: 'Partial', value: 15, color: '#FF9933' },
  { name: 'Non-Compliant', value: 7, color: '#ef4444' },
];

export default function Dashboard() {
  const navigate = useNavigate();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-gray-900 dark:text-white">Dashboard</h1>
          <p className="text-sm text-gray-500 dark:text-dark-muted mt-1">Welcome back! Here is your document intelligence overview.</p>
        </div>
        <button onClick={() => navigate('/upload')} className="btn-saffron flex items-center gap-2">
          <Upload className="w-4 h-4" />
          Upload Document
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, i) => (
          <StatsCard key={stat.title} {...stat} index={i} />
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Documents */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="lg:col-span-2 card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Recent Documents</h2>
            <button onClick={() => navigate('/documents')} className="text-sm text-primary-500 hover:text-primary-600 flex items-center gap-1">
              View all <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="space-y-1">
            {recentDocs.map((doc) => (
              <div key={doc.id} onClick={() => navigate(`/documents/${doc.id}`)} className="flex items-center gap-4 p-3 rounded-xl hover:bg-gray-50 dark:hover:bg-dark-bg cursor-pointer transition-colors">
                <div className="w-10 h-10 rounded-lg bg-primary-50 dark:bg-primary-900/20 flex items-center justify-center">
                  <FileText className="w-5 h-5 text-primary-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{doc.name}</p>
                  <p className="text-xs text-gray-500 dark:text-dark-muted">{doc.type}</p>
                </div>
                <ComplianceBadge status={doc.status} size="sm" />
                <span className="text-xs text-gray-400 hidden sm:block">{doc.time}</span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Compliance Health */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }} className="card">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Compliance Health</h2>
          <div className="flex justify-center">
            <ResponsiveContainer width={200} height={200}>
              <PieChart>
                <Pie data={complianceData} cx="50%" cy="50%" innerRadius={60} outerRadius={85} dataKey="value" strokeWidth={0}>
                  {complianceData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="text-center -mt-4 mb-4">
            <p className="text-3xl font-bold text-gray-900 dark:text-white">78%</p>
            <p className="text-sm text-gray-500 dark:text-dark-muted">Overall Score</p>
          </div>
          <div className="space-y-2">
            {complianceData.map((item) => (
              <div key={item.name} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                  <span className="text-gray-600 dark:text-dark-muted">{item.name}</span>
                </div>
                <span className="font-medium">{item.value}%</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Quick Actions */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }} className="card">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <button onClick={() => navigate('/upload')} className="flex items-center gap-3 p-4 rounded-xl border border-gray-200 dark:border-dark-border hover:border-saffron-300 hover:bg-saffron-50/50 dark:hover:bg-saffron-900/10 transition-all">
            <Upload className="w-5 h-5 text-saffron-500" />
            <span className="text-sm font-medium">Upload Documents</span>
          </button>
          <button onClick={() => navigate('/compliance')} className="flex items-center gap-3 p-4 rounded-xl border border-gray-200 dark:border-dark-border hover:border-green-300 hover:bg-green-50/50 dark:hover:bg-green-900/10 transition-all">
            <CheckCircle className="w-5 h-5 text-green-500" />
            <span className="text-sm font-medium">Check Compliance</span>
          </button>
          <button onClick={() => navigate('/analytics')} className="flex items-center gap-3 p-4 rounded-xl border border-gray-200 dark:border-dark-border hover:border-primary-300 hover:bg-primary-50/50 dark:hover:bg-primary-900/10 transition-all">
            <MessageSquare className="w-5 h-5 text-primary-500" />
            <span className="text-sm font-medium">View Analytics</span>
          </button>
        </div>
      </motion.div>
    </div>
  );
}
