import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, FileText, Download, RefreshCw, Share2, Copy, CheckCircle } from 'lucide-react';
import ComplianceBadge from '../components/ComplianceBadge';
import ChatInterface from '../components/ChatInterface';
import toast from 'react-hot-toast';

const mockDoc = {
  id: 1,
  filename: 'GST_Return_Q4_2025.pdf',
  type: 'GST Certificate',
  size: '2.4 MB',
  compliance_status: 'compliant',
  uploaded_at: '2025-07-29 10:30 AM',
  language: 'English',
  pages: 4,
  entities: [
    { type: 'GSTIN', value: '27AADCT2727Q1ZY', confidence: 0.98 },
    { type: 'PAN', value: 'AADCT2727Q', confidence: 0.96 },
    { type: 'Company Name', value: 'Tata Consultancy Services Ltd.', confidence: 0.99 },
    { type: 'Financial Year', value: '2024-25', confidence: 0.95 },
    { type: 'Total Tax', value: '₹14,52,340', confidence: 0.92 },
    { type: 'Filing Date', value: '25-Jul-2025', confidence: 0.97 },
  ],
  compliance: {
    score: 92,
    checks: [
      { rule: 'GSTIN Format Valid', passed: true },
      { rule: 'PAN-GSTIN Cross Verification', passed: true },
      { rule: 'Filing Deadline Met', passed: true },
      { rule: 'All Fields Present', passed: false, note: 'Missing HSN summary' },
    ],
  },
};

export default function DocumentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [copied, setCopied] = useState(null);

  const copyToClipboard = (value, key) => {
    navigator.clipboard.writeText(value);
    setCopied(key);
    toast.success('Copied to clipboard');
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <button onClick={() => navigate(-1)} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-border">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex-1">
          <h1 className="text-xl font-display font-bold text-gray-900 dark:text-white">{mockDoc.filename}</h1>
          <p className="text-sm text-gray-500 dark:text-dark-muted">{mockDoc.type} &bull; {mockDoc.size} &bull; {mockDoc.pages} pages</p>
        </div>
        <div className="flex items-center gap-2">
          <button className="btn-outline text-sm flex items-center gap-2" onClick={() => toast.success('Re-analyzing...')}>
            <RefreshCw className="w-4 h-4" /> Re-analyze
          </button>
          <button className="btn-primary text-sm flex items-center gap-2" onClick={() => toast.success('Report downloaded')}>
            <Download className="w-4 h-4" /> Download Report
          </button>
          <button className="p-2 rounded-lg border border-gray-200 dark:border-dark-border hover:bg-gray-50 dark:hover:bg-dark-bg" onClick={() => toast.success('Share link copied')}>
            <Share2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Preview + Entities */}
        <div className="lg:col-span-2 space-y-6">
          {/* Document Preview */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="card">
            <h2 className="text-lg font-semibold mb-4">Document Preview</h2>
            <div className="aspect-[3/4] max-h-[400px] bg-gray-100 dark:bg-dark-bg rounded-xl flex items-center justify-center border">
              <div className="text-center">
                <FileText className="w-16 h-16 text-gray-300 mx-auto mb-2" />
                <p className="text-sm text-gray-400">Document preview</p>
                <p className="text-xs text-gray-300">{mockDoc.filename}</p>
              </div>
            </div>
          </motion.div>

          {/* Extracted Entities */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="card">
            <h2 className="text-lg font-semibold mb-4">Extracted Entities</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {mockDoc.entities.map((entity, i) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-gray-50 dark:bg-dark-bg border border-gray-100 dark:border-dark-border">
                  <div>
                    <p className="text-xs text-gray-500 dark:text-dark-muted font-medium">{entity.type}</p>
                    <p className="text-sm font-semibold text-gray-900 dark:text-white mt-0.5">{entity.value}</p>
                    <div className="flex items-center gap-1 mt-1">
                      <div className="w-16 h-1.5 bg-gray-200 dark:bg-dark-border rounded-full overflow-hidden">
                        <div className="h-full bg-green-500 rounded-full" style={{ width: `${entity.confidence * 100}%` }} />
                      </div>
                      <span className="text-xs text-gray-400">{(entity.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                  <button onClick={() => copyToClipboard(entity.value, i)} className="p-1.5 rounded-lg hover:bg-gray-200 dark:hover:bg-dark-border">
                    {copied === i ? <CheckCircle className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4 text-gray-400" />}
                  </button>
                </div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* Right: Compliance + Chat */}
        <div className="space-y-6">
          {/* Compliance Status */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Compliance</h2>
              <ComplianceBadge status={mockDoc.compliance_status} />
            </div>
            <div className="text-center mb-4">
              <p className="text-4xl font-bold text-gray-900 dark:text-white">{mockDoc.compliance.score}%</p>
              <p className="text-sm text-gray-500 dark:text-dark-muted">Compliance Score</p>
            </div>
            <div className="space-y-2">
              {mockDoc.compliance.checks.map((check, i) => (
                <div key={i} className="flex items-start gap-2 p-2 rounded-lg">
                  <CheckCircle className={`w-4 h-4 mt-0.5 flex-shrink-0 ${check.passed ? 'text-green-500' : 'text-red-500'}`} />
                  <div>
                    <p className={`text-sm ${check.passed ? 'text-gray-700 dark:text-dark-text' : 'text-red-600 dark:text-red-400'}`}>{check.rule}</p>
                    {check.note && <p className="text-xs text-gray-400 mt-0.5">{check.note}</p>}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Chat */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
            <ChatInterface documentId={id} />
          </motion.div>
        </div>
      </div>
    </div>
  );
}
