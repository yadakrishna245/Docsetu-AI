import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { FileText, Image, File, Clock, MoreVertical } from 'lucide-react';
import ComplianceBadge from './ComplianceBadge';

const typeIcons = { pdf: FileText, jpg: Image, jpeg: Image, png: Image, default: File };

export default function DocumentCard({ document, viewMode = 'grid', index = 0 }) {
  const navigate = useNavigate();
  const ext = document.filename?.split('.').pop()?.toLowerCase() || 'default';
  const Icon = typeIcons[ext] || typeIcons.default;

  if (viewMode === 'list') {
    return (
      <motion.div
        initial={{ opacity: 0, x: -10 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: index * 0.05 }}
        onClick={() => navigate(`/documents/${document.id}`)}
        className="flex items-center gap-4 px-4 py-3 rounded-xl hover:bg-gray-50 dark:hover:bg-dark-bg cursor-pointer transition-colors"
      >
        <div className="w-10 h-10 rounded-lg bg-primary-50 dark:bg-primary-900/20 flex items-center justify-center">
          <Icon className="w-5 h-5 text-primary-500" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{document.filename}</p>
          <p className="text-xs text-gray-500 dark:text-dark-muted">{document.type} &bull; {document.size}</p>
        </div>
        <ComplianceBadge status={document.compliance_status} />
        <div className="flex items-center gap-1 text-xs text-gray-400">
          <Clock className="w-3.5 h-3.5" />
          <span>{document.uploaded_at}</span>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      onClick={() => navigate(`/documents/${document.id}`)}
      className="card-hover group"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-50 to-saffron-50 dark:from-primary-900/20 dark:to-saffron-900/20 flex items-center justify-center">
          <Icon className="w-6 h-6 text-primary-500" />
        </div>
        <button className="p-1 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-gray-100 dark:hover:bg-dark-border transition-all">
          <MoreVertical className="w-4 h-4 text-gray-400" />
        </button>
      </div>
      <h3 className="text-sm font-semibold text-gray-900 dark:text-white truncate mb-1">{document.filename}</h3>
      <p className="text-xs text-gray-500 dark:text-dark-muted mb-3">{document.type} &bull; {document.size}</p>
      <div className="flex items-center justify-between">
        <ComplianceBadge status={document.compliance_status} size="sm" />
        <span className="text-xs text-gray-400">{document.uploaded_at}</span>
      </div>
    </motion.div>
  );
}
