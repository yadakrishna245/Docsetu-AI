import { useState } from 'react';
import { motion } from 'framer-motion';
import { Upload as UploadIcon, FileText, Languages, Loader2, CheckCircle2 } from 'lucide-react';
import toast from 'react-hot-toast';
import FileUploader from '../components/FileUploader';
import { LANGUAGES, DOCUMENT_TYPES } from '../utils/constants';

export default function Upload() {
  const [files, setFiles] = useState([]);
  const [language, setLanguage] = useState('en');
  const [docType, setDocType] = useState('');
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploadComplete, setUploadComplete] = useState(false);

  const handleFilesSelected = (selectedFiles) => {
    setFiles((prev) => [...prev, ...selectedFiles]);
    setUploadComplete(false);
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      toast.error('Please select files to upload');
      return;
    }
    setUploading(true);
    setProgress(0);

    // Simulate upload progress
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setUploading(false);
          setUploadComplete(true);
          toast.success(`${files.length} document(s) uploaded successfully!`);
          return 100;
        }
        return prev + 5;
      });
    }, 150);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-display font-bold text-gray-900 dark:text-white">Upload Documents</h1>
        <p className="text-sm text-gray-500 dark:text-dark-muted mt-1">Upload Indian documents for AI analysis, OCR extraction, and compliance checking.</p>
      </div>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="card">
        <FileUploader onFilesSelected={handleFilesSelected} />
      </motion.div>

      {/* Settings */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="card space-y-4">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <Languages className="w-5 h-5 text-saffron-500" />
          Processing Options
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-dark-text mb-1.5">OCR Language</label>
            <select value={language} onChange={(e) => setLanguage(e.target.value)} className="input-field">
              {LANGUAGES.map((lang) => (
                <option key={lang.value} value={lang.value}>{lang.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-dark-text mb-1.5">Document Type</label>
            <select value={docType} onChange={(e) => setDocType(e.target.value)} className="input-field">
              <option value="">Auto-detect</option>
              {DOCUMENT_TYPES.map((type) => (
                <option key={type.value} value={type.value}>{type.label}</option>
              ))}
            </select>
          </div>
        </div>
      </motion.div>

      {/* Progress */}
      {(uploading || uploadComplete) && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">
              {uploadComplete ? 'Upload Complete!' : 'Uploading...'}
            </span>
            <span className="text-sm text-gray-500">{progress}%</span>
          </div>
          <div className="w-full h-2 bg-gray-200 dark:bg-dark-border rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              className={`h-full rounded-full ${uploadComplete ? 'bg-green-500' : 'bg-gradient-to-r from-saffron-400 to-saffron-600'}`}
            />
          </div>
          {uploadComplete && (
            <div className="flex items-center gap-2 mt-3 text-green-600">
              <CheckCircle2 className="w-5 h-5" />
              <span className="text-sm font-medium">{files.length} document(s) ready for analysis</span>
            </div>
          )}
        </motion.div>
      )}

      {/* Upload Button */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
        <button
          onClick={handleUpload}
          disabled={files.length === 0 || uploading}
          className="w-full btn-saffron py-3 text-base flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {uploading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Uploading & Analyzing...
            </>
          ) : (
            <>
              <UploadIcon className="w-5 h-5" />
              Upload & Analyze ({files.length} file{files.length !== 1 ? 's' : ''})
            </>
          )}
        </button>
      </motion.div>
    </div>
  );
}
