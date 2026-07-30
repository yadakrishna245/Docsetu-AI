import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { FileText, CheckCircle, AlertTriangle, MessageSquare, Upload, ArrowRight, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import StatsCard from '../components/StatsCard';
import ComplianceBadge from '../components/ComplianceBadge';
import { documentAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function Dashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [documents, setDocuments] = useState([]);
  const [totalDocs, setTotalDocs] = useState(0);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const docsRes = await documentAPI.getAll({ page: 1, page_size: 5 });
      setDocuments(docsRes.data.documents || []);
      setTotalDocs(docsRes.data.total || 0);
    } catch (error) {
      console.log('Dashboard fetch error:', error);
    } finally {
      setLoading(false);
    }
  };

  const analyzedCount = documents.filter(d => d.status === 'processed').length;
  const issuesCount = documents.filter(d => d.status === 'failed').length;

  const stats = [
    { title: 'Total Documents', value: totalDocs.toString(), icon: FileText, trend: 'up', trendValue: totalDocs > 0 ? `${totalDocs} total` : 'Upload to start', color: 'primary' },
    { title: 'Processed', value: analyzedCount.toString(), icon: CheckCircle, trend: 'up', trendValue: totalDocs > 0 ? `${Math.round((analyzedCount/Math.max(totalDocs,1))*100)}% done` : 'None yet', color: 'green' },
    { title: 'Issues Found', value: issuesCount.toString(), icon: AlertTriangle, trend: 'down', trendValue: issuesCount === 0 ? 'All clear' : 'Needs review', color: 'saffron' },
    { title: 'AI Queries', value: '0', icon: MessageSquare, trend: 'up', trendValue: 'Ask questions', color: 'purple' },
  ];

  const complianceData = totalDocs > 0
    ? [
        { name: 'Processed', value: analyzedCount, color: '#138808' },
        { name: 'Pending', value: totalDocs - analyzedCount - issuesCount, color: '#FF9933' },
        { name: 'Failed', value: issuesCount, color: '#ef4444' },
      ]
    : [
        { name: 'No Data', value: 100, color: '#e5e7eb' },
      ];

  const overallScore = totalDocs > 0 ? Math.round((analyzedCount / Math.max(totalDocs, 1)) * 100) : 0;

  const getTimeAgo = (dateStr) => {
    if (!dateStr) return '';
    const now = new Date();
    const date = new Date(dateStr);
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    return `${Math.floor(diffHours / 24)} day${Math.floor(diffHours/24) > 1 ? 's' : ''} ago`;
  };

  const getDocStatus = (status) => {
    switch(status) {
      case 'processed': return 'compliant';
      case 'uploaded': return 'pending';
      case 'processing': return 'pending';
      case 'failed': return 'non_compliant';
      default: return 'pending';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-gray-900 dark:text-white">Dashboard</h1>
          <p className="text-sm text-gray-500 dark:text-dark-muted mt-1">
            Welcome back{user?.full_name ? `, ${user.full_name}` : ''}! Here is your document intelligence overview.
          </p>
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
          {documents.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
              <p className="text-gray-500 dark:text-dark-muted mb-2">No documents uploaded yet</p>
              <p className="text-sm text-gray-400">Upload your first document to get started with AI analysis</p>
              <button onClick={() => navigate('/upload')} className="mt-4 px-4 py-2 bg-saffron-500 text-white rounded-lg text-sm hover:bg-saffron-600 transition-colors">
                Upload Now
              </button>
            </div>
          ) : (
            <div className="space-y-1">
              {documents.map((doc) => (
                <div key={doc.id} onClick={() => navigate(`/documents/${doc.id}`)} className="flex items-center gap-4 p-3 rounded-xl hover:bg-gray-50 dark:hover:bg-dark-bg cursor-pointer transition-colors">
                  <div className="w-10 h-10 rounded-lg bg-primary-50 dark:bg-primary-900/20 flex items-center justify-center">
                    <FileText className="w-5 h-5 text-primary-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{doc.original_filename || doc.filename}</p>
                    <p className="text-xs text-gray-500 dark:text-dark-muted">{doc.file_type?.toUpperCase()} • {doc.file_size ? `${(doc.file_size / 1024).toFixed(1)} KB` : ''}</p>
                  </div>
                  <ComplianceBadge status={getDocStatus(doc.status)} size="sm" />
                  <span className="text-xs text-gray-400 hidden sm:block">{getTimeAgo(doc.created_at)}</span>
                </div>
              ))}
            </div>
          )}
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
            <p className="text-3xl font-bold text-gray-900 dark:text-white">{overallScore}%</p>
            <p className="text-sm text-gray-500 dark:text-dark-muted">{totalDocs > 0 ? 'Overall Score' : 'Upload documents to start'}</p>
          </div>
          <div className="space-y-2">
            {totalDocs > 0 ? complianceData.map((item) => (
              <div key={item.name} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                  <span className="text-gray-600 dark:text-dark-muted">{item.name}</span>
                </div>
                <span className="font-medium">{item.value}</span>
              </div>
            )) : (
              <p className="text-center text-sm text-gray-400">No compliance data yet</p>
            )}
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
