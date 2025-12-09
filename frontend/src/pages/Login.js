import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import api from '../utils/api';
import { useAuth } from '../context/AuthContext';
import SEO from '../components/SEO';

const Login = () => {
  const navigate = useNavigate();
  const { login, isAuthenticated } = useAuth();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    otp: '',
  });

  // Redirect if already logged in
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await api.post('/auth/login', {
        email: formData.email,
        password: formData.password,
      });
      toast.success(response.data.message);
      setStep(2);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await api.post('/auth/verify-login', {
        email: formData.email,
        otp: formData.otp,
      });
      
      login(response.data.access_token, response.data.user);
      toast.success('Login successful!');
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'OTP verification failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      <SEO
        title="Login - MailGuard"
        description="Sign in to your MailGuard account to access email verification dashboard"
        noindex={true}
      />
      <div className="flex-1 flex items-center justify-center p-8 bg-white">
        <div className="w-full max-w-md">
          <div className="mb-8">
            <Link to="/" className="flex items-center space-x-2 mb-8">
              <Mail className="h-8 w-8 text-blue-600" />
              <span className="text-2xl font-bold text-gray-900">MailGuard</span>
            </Link>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Welcome back</h1>
            <p className="text-gray-600">Sign in to your account</p>
          </div>

          {step === 1 ? (
            <form onSubmit={handleLogin} className="space-y-4" data-testid="login-form">
              <div>
                <Label htmlFor="email">Email</Label>
                <div className="relative mt-1">
                  <Mail className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    required
                    className="pl-10"
                    placeholder="you@example.com"
                    value={formData.email}
                    onChange={handleChange}
                    data-testid="login-email-input"
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <Label htmlFor="password">Password</Label>
                  <Link to="/forgot-password" className="text-sm text-blue-600 hover:text-blue-700">
                    Forgot password?
                  </Link>
                </div>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                  <Input
                    id="password"
                    name="password"
                    type="password"
                    required
                    className="pl-10"
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={handleChange}
                    data-testid="login-password-input"
                  />
                </div>
              </div>

              <Button type="submit" className="w-full" disabled={loading} data-testid="login-submit-btn">
                {loading ? 'Sending OTP...' : 'Continue'}
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </form>
          ) : (
            <form onSubmit={handleVerifyOTP} className="space-y-4" data-testid="login-otp-form">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                <p className="text-sm text-blue-800">
                  We've sent a verification code to <strong>{formData.email}</strong>
                </p>
              </div>

              <div>
                <Label htmlFor="otp">Verification Code</Label>
                <Input
                  id="otp"
                  name="otp"
                  type="text"
                  required
                  placeholder="Enter 6-digit code"
                  value={formData.otp}
                  onChange={handleChange}
                  maxLength={6}
                  data-testid="login-otp-input"
                  className="text-center text-2xl tracking-widest"
                />
              </div>

              <Button type="submit" className="w-full" disabled={loading} data-testid="login-verify-otp-btn">
                {loading ? 'Verifying...' : 'Verify & Login'}
              </Button>

              <Button
                type="button"
                variant="ghost"
                className="w-full"
                onClick={() => setStep(1)}
              >
                Back to login
              </Button>
            </form>
          )}

          <div className="mt-6 text-center text-sm text-gray-600">
            Don't have an account?{' '}
            <Link to="/register" className="text-blue-600 hover:text-blue-700 font-medium">
              Sign up
            </Link>
          </div>
        </div>
      </div>

      <div className="hidden lg:flex flex-1 bg-gradient-to-br from-purple-600 to-pink-600 items-center justify-center p-12">
        <div className="text-white max-w-lg">
          <h2 className="text-4xl font-bold mb-6" style={{fontFamily: 'Space Grotesk, sans-serif'}}>
            Secure Authentication
          </h2>
          <p className="text-xl text-purple-100 mb-8">
            We use two-factor authentication to keep your account secure.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
