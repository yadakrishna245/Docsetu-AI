import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sparkles, Mail, Lock, Eye, EyeOff, Loader2, User, Building } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Register() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [organization, setOrganization] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      return;
    }
    setLoading(true);
    const result = await register(name, email, password, organization);
    setLoading(false);
    if (result.success) navigate('/');
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-8 bg-gray-50 dark:bg-dark-bg">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">
        <div className="flex items-center gap-3 mb-8 justify-center">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-saffron-500 flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-xl font-display font-bold text-gray-900 dark:text-white">DocSetu AI</h1>
        </div>

        <div className="card">
          <h2 className="text-2xl font-display font-bold text-gray-900 dark:text-white mb-2">Create Account</h2>
          <p className="text-gray-500 dark:text-dark-muted mb-6">Start analyzing documents with AI</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-dark-text mb-1.5">Full Name</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Enter your name" className="input-field pl-11" required />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-dark-text mb-1.5">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="name@company.com" className="input-field pl-11" required />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-dark-text mb-1.5">Organization</label>
              <div className="relative">
                <Building className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input type="text" value={organization} onChange={(e) => setOrganization(e.target.value)} placeholder="Your company name" className="input-field pl-11" />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-dark-text mb-1.5">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input type={showPassword ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Create a password" className="input-field pl-11 pr-11" required />
                <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-dark-text mb-1.5">Confirm Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} placeholder="Confirm password" className="input-field pl-11" required />
              </div>
              {confirmPassword && password !== confirmPassword && (
                <p className="text-xs text-red-500 mt-1">Passwords do not match</p>
              )}
            </div>

            <button type="submit" disabled={loading || password !== confirmPassword} className="w-full btn-saffron py-3 text-base flex items-center justify-center gap-2 disabled:opacity-50">
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Create Account'}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-gray-500 dark:text-dark-muted">
            Already have an account?{' '}
            <Link to="/login" className="text-saffron-500 hover:text-saffron-600 font-medium">Sign in</Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
