import { motion } from 'framer-motion';
import { Shield, CheckCircle, XCircle, AlertTriangle, Lightbulb, ExternalLink } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

const overallScore = 78;
const scoreData = [
  { name: 'Score', value: overallScore, color: '#138808' },
  { name: 'Remaining', value: 100 - overallScore, color: '#e5e7eb' },
];

const rules = [
  { id: 1, name: 'GST Filing Compliance', description: 'All GST returns filed within deadlines', status: 'pass', documents: 45 },
  { id: 2, name: 'PAN-Aadhaar Linkage', description: 'PAN linked with Aadhaar for all entities', status: 'pass', documents: 32 },
  { id: 3, name: 'Invoice Format (e-Invoice)', description: 'Invoices follow GST e-Invoice schema', status: 'fail', documents: 12 },
  { id: 4, name: 'TDS Compliance', description: 'TDS deducted and deposited correctly', status: 'pass', documents: 28 },
  { id: 5, name: 'KYC Document Validity', description: 'All KYC documents within validity period', status: 'warning', documents: 8 },
  { id: 6, name: 'Digital Signature Verification', description: 'Documents with valid digital signatures', status: 'pass', documents: 56 },
  { id: 7, name: 'FEMA Compliance', description: 'Foreign exchange documentation complete', status: 'fail', documents: 5 },
];

const recommendations = [
  { id: 1, priority: 'high', text: 'Update 12 invoices to e-Invoice format before August 15th deadline' },
  { id: 2, priority: 'high', text: 'Resolve FEMA documentation gaps for 5 transactions' },
  { id: 3, priority: 'medium', text: 'Renew 8 KYC documents expiring in next 30 days' },
  { id: 4, priority: 'low', text: 'Consider enabling auto-verification for PAN-GSTIN cross-checks' },
];

const updates = [
  { id: 1, title: 'GST Council 53rd Meeting Updates', date: 'Jul 25, 2025', tag: 'GST' },
  { id: 2, title: 'New e-Invoice threshold: Rs. 5 Crore', date: 'Jul 20, 2025', tag: 'Invoice' },
  { id: 3, title: 'RBI Guidelines on Digital KYC', date: 'Jul 15, 2025', tag: 'KYC' },
];

export default function Compliance() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-display font-bold text-gray-900 dark:text-white">Compliance Dashboard</h1>
        <p className="text-sm text-gray-500 dark:text-dark-muted mt-1">Monitor regulatory compliance across all your documents.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Score */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="card text-center">
          <h2 className="text-lg font-semibold mb-2">Overall Compliance Score</h2>
          <div className="relative inline-block">
            <ResponsiveContainer width={180} height={180}>
              <PieChart>
                <Pie data={scoreData} cx="50%" cy="50%" innerRadius={65} outerRadius={80} dataKey="value" startAngle={90} endAngle={-270} strokeWidth={0}>
                  {scoreData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex items-center justify-center">
              <div>
                <p className="text-3xl font-bold text-gray-900 dark:text-white">{overallScore}%</p>
                <p className="text-xs text-gray-500">Compliant</p>
              </div>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-2 mt-4">
            <div className="text-center p-2 rounded-lg bg-green-50 dark:bg-green-900/20">
              <p className="text-lg font-bold text-green-600">5</p>
              <p className="text-xs text-gray-500">Passing</p>
            </div>
            <div className="text-center p-2 rounded-lg bg-yellow-50 dark:bg-yellow-900/20">
              <p className="text-lg font-bold text-yellow-600">1</p>
              <p className="text-xs text-gray-500">Warning</p>
            </div>
            <div className="text-center p-2 rounded-lg bg-red-50 dark:bg-red-900/20">
              <p className="text-lg font-bold text-red-600">2</p>
              <p className="text-xs text-gray-500">Failing</p>
            </div>
          </div>
        </motion.div>

        {/* Rules */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="lg:col-span-2 card">
          <h2 className="text-lg font-semibold mb-4">Compliance Rules</h2>
          <div className="space-y-2">
            {rules.map((rule) => (
              <div key={rule.id} className="flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50 dark:hover:bg-dark-bg transition-colors">
                {rule.status === 'pass' && <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />}
                {rule.status === 'fail' && <XCircle className="w-5 h-5 text-red-500 flex-shrink-0" />}
                {rule.status === 'warning' && <AlertTriangle className="w-5 h-5 text-yellow-500 flex-shrink-0" />}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">{rule.name}</p>
                  <p className="text-xs text-gray-500 dark:text-dark-muted">{rule.description}</p>
                </div>
                <span className="text-xs text-gray-400">{rule.documents} docs</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recommendations */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="card">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-saffron-500" />
            Recommendations
          </h2>
          <div className="space-y-3">
            {recommendations.map((rec) => (
              <div key={rec.id} className="flex items-start gap-3 p-3 rounded-xl bg-gray-50 dark:bg-dark-bg">
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                  rec.priority === 'high' ? 'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400' :
                  rec.priority === 'medium' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400' :
                  'bg-blue-100 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400'
                }`}>{rec.priority}</span>
                <p className="text-sm text-gray-700 dark:text-dark-text">{rec.text}</p>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Regulatory Updates */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="card">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Shield className="w-5 h-5 text-primary-500" />
            Regulatory Updates
          </h2>
          <div className="space-y-3">
            {updates.map((update) => (
              <div key={update.id} className="flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50 dark:hover:bg-dark-bg transition-colors cursor-pointer group">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900 dark:text-white group-hover:text-primary-500 transition-colors">{update.title}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-gray-400">{update.date}</span>
                    <span className="px-1.5 py-0.5 bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400 text-xs rounded">{update.tag}</span>
                  </div>
                </div>
                <ExternalLink className="w-4 h-4 text-gray-300 group-hover:text-primary-500 transition-colors" />
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
