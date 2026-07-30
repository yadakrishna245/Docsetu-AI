import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileText, Image, X, CheckCircle } from 'lucide-react';

export default function FileUploader({ onFilesSelected, maxFiles = 10, accept }) {
  const [files, setFiles] = useState([]);

  const onDrop = useCallback((acceptedFiles) => {
    const newFiles = acceptedFiles.map((file) => ({
      file,
      id: `${file.name}-${Date.now()}`,
      progress: 0,
      status: 'pending',
    }));
    setFiles((prev) => [...prev, ...newFiles]);
    onFilesSelected?.(acceptedFiles);
  }, [onFilesSelected]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxFiles,
    accept: accept || {
      'application/pdf': ['.pdf'],
      'image/*': ['.jpg', '.jpeg', '.png', '.tiff'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
  });

  const removeFile = (id) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const getFileIcon = (name) => {
    const ext = name.split('.').pop().toLowerCase();
    if (['jpg', 'jpeg', 'png', 'tiff'].includes(ext)) return Image;
    return FileText;
  };

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-300 ${
          isDragActive
            ? 'border-saffron-500 bg-saffron-50 dark:bg-saffron-900/10'
            : 'border-gray-300 dark:border-dark-border hover:border-primary-400 hover:bg-primary-50/50 dark:hover:bg-primary-900/10'
        }`}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-3">
          <div className={`w-16 h-16 rounded-2xl flex items-center justify-center transition-colors ${
            isDragActive ? 'bg-saffron-100 dark:bg-saffron-900/20' : 'bg-gray-100 dark:bg-dark-border'
          }`}>
            <Upload className={`w-8 h-8 ${isDragActive ? 'text-saffron-500' : 'text-gray-400'}`} />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-700 dark:text-dark-text">
              {isDragActive ? 'Drop files here...' : 'Drag & drop files here'}
            </p>
            <p className="text-xs text-gray-500 dark:text-dark-muted mt-1">
              or click to browse. Supports PDF, Images, Word docs
            </p>
          </div>
          <div className="flex gap-2 mt-2">
            {['PDF', 'JPG', 'PNG', 'DOCX', 'TIFF'].map((type) => (
              <span key={type} className="px-2 py-0.5 bg-gray-100 dark:bg-dark-border rounded text-xs text-gray-500 dark:text-dark-muted">
                {type}
              </span>
            ))}
          </div>
        </div>
      </div>

      <AnimatePresence>
        {files.length > 0 && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="space-y-2">
            {files.map((f) => {
              const Icon = getFileIcon(f.file.name);
              return (
                <motion.div
                  key={f.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 dark:bg-dark-bg border border-gray-100 dark:border-dark-border"
                >
                  <Icon className="w-5 h-5 text-primary-500 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{f.file.name}</p>
                    <p className="text-xs text-gray-400">{(f.file.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                  {f.status === 'done' ? (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  ) : (
                    <button onClick={() => removeFile(f.id)} className="p-1 rounded-lg hover:bg-gray-200 dark:hover:bg-dark-border">
                      <X className="w-4 h-4 text-gray-400" />
                    </button>
                  )}
                </motion.div>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
