import { CheckCircle, XCircle, AlertCircle, Clock } from 'lucide-react';

const statusConfig = {
  compliant: {
    label: 'Compliant',
    icon: CheckCircle,
    classes: 'bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400 border-green-200 dark:border-green-800',
  },
  non_compliant: {
    label: 'Non-Compliant',
    icon: XCircle,
    classes: 'bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400 border-red-200 dark:border-red-800',
  },
  partial: {
    label: 'Partial',
    icon: AlertCircle,
    classes: 'bg-yellow-50 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400 border-yellow-200 dark:border-yellow-800',
  },
  pending: {
    label: 'Pending',
    icon: Clock,
    classes: 'bg-gray-50 text-gray-700 dark:bg-gray-900/20 dark:text-gray-400 border-gray-200 dark:border-gray-700',
  },
};

export default function ComplianceBadge({ status = 'pending', size = 'md' }) {
  const config = statusConfig[status] || statusConfig.pending;
  const Icon = config.icon;
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs gap-1',
    md: 'px-2.5 py-1 text-xs gap-1.5',
    lg: 'px-3 py-1.5 text-sm gap-2',
  };

  return (
    <span className={`inline-flex items-center rounded-full border font-medium ${config.classes} ${sizeClasses[size]}`}>
      <Icon className={size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5'} />
      {config.label}
    </span>
  );
}
