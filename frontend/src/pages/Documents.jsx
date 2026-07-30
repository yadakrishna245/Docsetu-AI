import { useState } from 'react';
import { motion } from 'framer-motion';
import { Search, Grid3X3, List, Filter, ChevronLeft, ChevronRight } from 'lucide-react';
import DocumentCard from '../components/DocumentCard';

const mockDocuments = [
  { id: 1, filename: 'GST_Return_Q4_2025.pdf', type: 'GST Certificate', size: '2.4 MB', compliance_status: 'compliant', uploaded_at: '2 hours ago' },
  { id: 2, filename: 'PAN_Verification_Sharma.pdf', type: 'PAN Card', size: '1.1 MB', compliance_status: 'compliant', uploaded_at: '5 hours ago' },
  { id: 3, filename: 'Invoice_Tata_Motors.pdf', type: 'Invoice', size: '3.2 MB', compliance_status: 'partial', uploaded_at: '1 day ago' },
  { id: 4, filename: 'Bank_Statement_SBI.pdf', type: 'Bank Statement', size: '5.8 MB', compliance_status: 'non_compliant', uploaded_at: '2 days ago' },
  { id: 5, filename: 'ITR_2024_25.pdf', type: 'Income Tax Return', size: '4.1 MB', compliance_status: 'pending', uploaded_at: '3 days ago' },
  { id: 6, filename: 'Aadhaar_Kumar_Ravi.jpg', type: 'Aadhaar Card', size: '0.8 MB', compliance_status: 'compliant', uploaded_at: '4 days ago' },
  { id: 7, filename: 'Contract_Infosys.pdf', type: 'Contract', size: '7.2 MB', compliance_status: 'partial', uploaded_at: '5 days ago' },
  { id: 8, filename: 'DL_Maharashtra.png', type: 'Driving License', size: '1.5 MB', compliance_status: 'compliant', uploaded_at: '1 week ago' },
];

export default function Documents() {
  const [viewMode, setViewMode] = useState('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);

  const filtered = mockDocuments.filter((doc) => {
    const matchesSearch = doc.filename.toLowerCase().includes(searchQuery.toLowerCase()) || doc.type.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = filterStatus === 'all' || doc.compliance_status === filterStatus;
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-display font-bold text-gray-900 dark:text-white">Documents</h1>
        <p className="text-sm text-gray-500 dark:text-dark-muted mt-1">Manage and view all your uploaded documents.</p>
      </div>

      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center justify-between">
        <div className="flex items-center gap-3 flex-1 w-full sm:w-auto">
          <div className="relative flex-1 sm:max-w-xs">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search documents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input-field pl-10"
            />
          </div>
          <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)} className="input-field w-auto">
            <option value="all">All Status</option>
            <option value="compliant">Compliant</option>
            <option value="partial">Partial</option>
            <option value="non_compliant">Non-Compliant</option>
            <option value="pending">Pending</option>
          </select>
        </div>
        <div className="flex items-center gap-1 bg-gray-100 dark:bg-dark-bg p-1 rounded-lg">
          <button onClick={() => setViewMode('grid')} className={`p-2 rounded-md transition-colors ${viewMode === 'grid' ? 'bg-white dark:bg-dark-card shadow-sm' : ''}`}>
            <Grid3X3 className="w-4 h-4" />
          </button>
          <button onClick={() => setViewMode('list')} className={`p-2 rounded-md transition-colors ${viewMode === 'list' ? 'bg-white dark:bg-dark-card shadow-sm' : ''}`}>
            <List className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Documents Grid/List */}
      {filtered.length === 0 ? (
        <div className="card text-center py-12">
          <Filter className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 dark:text-dark-muted font-medium">No documents found</p>
          <p className="text-sm text-gray-400 mt-1">Try adjusting your search or filter criteria</p>
        </div>
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filtered.map((doc, i) => (
            <DocumentCard key={doc.id} document={doc} viewMode="grid" index={i} />
          ))}
        </div>
      ) : (
        <div className="card divide-y divide-gray-100 dark:divide-dark-border">
          {filtered.map((doc, i) => (
            <DocumentCard key={doc.id} document={doc} viewMode="list" index={i} />
          ))}
        </div>
      )}

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">Showing {filtered.length} of {mockDocuments.length} documents</p>
        <div className="flex items-center gap-2">
          <button disabled={currentPage === 1} onClick={() => setCurrentPage((p) => p - 1)} className="p-2 rounded-lg border border-gray-200 dark:border-dark-border disabled:opacity-50 hover:bg-gray-50 dark:hover:bg-dark-bg">
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="px-3 py-1 text-sm font-medium bg-primary-500 text-white rounded-lg">1</span>
          <button disabled className="p-2 rounded-lg border border-gray-200 dark:border-dark-border disabled:opacity-50 hover:bg-gray-50 dark:hover:bg-dark-bg">
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
