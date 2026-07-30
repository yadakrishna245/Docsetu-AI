import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sparkles, Mail, Lock, Eye, EyeOff, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const result = await login(email, password);
    setLoading(false);
    if (result.success) navigate('/');
  };

  return (
    <div className="min-h-screen flex">
      {/* Left Panel - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary-500 via-primary-600 to-primary-800 relative overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-20 left-20 w-64 h-64 rounded-full bg-saffron-500 blur-3xl" />
          <div className="absolute bottom-20 right-20 w-96 h-96 rounded-full bg-green-500 blur-3xl" />
        </div>
        <div className="relative z-10 flex flex-col justify-center px-16 text-white">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-12 h-12 rounded-xl bg-white/20 backdrop-blur flex items-center justify-center">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-display font-bold">DocSetu AI</h1>
              <p className="text-sm text-white/70">Document Intelligence Platform</p>
            </div>
          </div>
          <h2 className="text-4xl font-display font-bold leading-tight mb-4">
            AI-Powered Document Intelligence for India
          </h2>
          <p className="text-lg text-white/80 leading-relaxed">
            Analyze PAN, GST, Aadhaar, and more. Extract entities, check compliance, and get AI-powered insights from your documents.
          </p>
          <div className="mt-8 flex items-center gap-6">
            <div className="text-center">
              <p className="text-2xl font-bold">50K+</p>
              <p className="text-xs text-white/60">Docs Processed</p>
            </div>
            <div className="w-px h-10 bg-white/20" />
            <div className="text-center">
              <p className="text-2xl font-bold">99.2%</p>
              <p className="text-xs text-white/60">Accuracy</p>
            </div>
            <div className="w-px h-10 bg-white/20" />
            <div className="text-center">
              <p className="text-2xl font-bold">12+</p>
              <p className="text-xs text-white/60">Languages</p>
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel - Form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-gray-50 dark:bg-dark-bg">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">
          <div className="lg:hidden flex items-center gap-3 mb-8 justify-center">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-saffron-500 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-xl font-display font-bold">DocSetu AI</h1>
          </div>

          <h2 className="text-2xl font-display font-bold text-gray-900 dark:text-white mb-2">Welcome back</h2>
          <p className="text-gray-500 dark:text-dark-muted mb-8">Sign in to your account to continue</p>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-dark-text mb-1.5">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  className="input-field pl-11"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-dark-text mb-1.5">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="input-field pl-11 pr-11"
                  required
                />
                <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" className="w-4 h-4 rounded border-gray-300 text-primary-500 focus:ring-primary-500" />
                <span className="text-sm text-gray-600 dark:text-dark-muted">Remember me</span>
              </label>
              <a href="#" className="text-sm text-saffron-500 hover:text-saffron-600 font-medium">Forgot password?</a>
            </div>

            <button type="submit" disabled={loading} className="w-full btn-saffron py-3 text-base flex items-center justify-center gap-2">
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Sign In'}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-gray-500 dark:text-dark-muted">
            Don't have an account?{' '}
            <Link to="/register" className="text-saffron-500 hover:text-saffron-600 font-medium">Create account</Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
