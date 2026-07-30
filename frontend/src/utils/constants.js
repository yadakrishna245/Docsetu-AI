export const COLORS = {
  primary: '#000080',
  saffron: '#FF9933',
  green: '#138808',
  white: '#FFFFFF',
  navy: '#000080',
};

export const ROUTES = {
  DASHBOARD: '/',
  UPLOAD: '/upload',
  DOCUMENTS: '/documents',
  DOCUMENT_DETAIL: '/documents/:id',
  COMPLIANCE: '/compliance',
  ANALYTICS: '/analytics',
  LOGIN: '/login',
  REGISTER: '/register',
};

export const DOCUMENT_TYPES = [
  { value: 'aadhaar', label: 'Aadhaar Card' },
  { value: 'pan', label: 'PAN Card' },
  { value: 'gst', label: 'GST Certificate' },
  { value: 'invoice', label: 'Invoice' },
  { value: 'contract', label: 'Contract' },
  { value: 'bank_statement', label: 'Bank Statement' },
  { value: 'itr', label: 'Income Tax Return' },
  { value: 'driving_license', label: 'Driving License' },
  { value: 'passport', label: 'Passport' },
  { value: 'other', label: 'Other' },
];

export const LANGUAGES = [
  { value: 'en', label: 'English' },
  { value: 'hi', label: 'Hindi (हिन्दी)' },
  { value: 'ta', label: 'Tamil (தமிழ்)' },
  { value: 'te', label: 'Telugu (తెలుగు)' },
  { value: 'bn', label: 'Bengali (বাংলা)' },
  { value: 'mr', label: 'Marathi (मराठी)' },
  { value: 'gu', label: 'Gujarati (ગુજરાતી)' },
  { value: 'kn', label: 'Kannada (ಕನ್ನಡ)' },
  { value: 'ml', label: 'Malayalam (മലയാളം)' },
  { value: 'pa', label: 'Punjabi (ਪੰਜਾਬੀ)' },
];

export const COMPLIANCE_STATUS = {
  COMPLIANT: { label: 'Compliant', color: 'green' },
  NON_COMPLIANT: { label: 'Non-Compliant', color: 'red' },
  PARTIAL: { label: 'Partially Compliant', color: 'yellow' },
  PENDING: { label: 'Pending Review', color: 'gray' },
};

export const DOCUMENT_STATUS = {
  UPLOADED: { label: 'Uploaded', color: 'blue' },
  PROCESSING: { label: 'Processing', color: 'yellow' },
  ANALYZED: { label: 'Analyzed', color: 'green' },
  FAILED: { label: 'Failed', color: 'red' },
};

export const FILE_TYPES = {
  pdf: { icon: 'FileText', color: '#ef4444' },
  jpg: { icon: 'Image', color: '#3b82f6' },
  jpeg: { icon: 'Image', color: '#3b82f6' },
  png: { icon: 'Image', color: '#8b5cf6' },
  doc: { icon: 'FileText', color: '#2563eb' },
  docx: { icon: 'FileText', color: '#2563eb' },
  tiff: { icon: 'Image', color: '#6366f1' },
};
