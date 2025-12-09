import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, ArrowLeft, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import api from '../utils/api';
import SEO from '../components/SEO';

const ForgotPassword = () => {
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await api.post('/auth/forgot-password', { email });
      toast.success(response.data.message);
      setSent(true);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send reset email');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      <SEO
        title="Forgot Password - MailGuard"
        description="Reset your MailGuard password"
        noindex={true}
      />
      <div className="flex-1 flex items-center justify-center p-8 bg-white">
        <div className="w-full max-w-md">
          <div className="mb-8">
            <Link to="/" className="flex items-center space-x-2 mb-8">
              <Mail className="h-8 w-8 text-blue-600" />
              <span className="text-2xl font-bold text-gray-900">MailGuard</span>
            </Link>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Forgot Password?</h1>
            <p className="text-gray-600">
              {sent ? 'Check your email' : "Enter your email and we'll send you a reset link"}
            </p>
          </div>

          {sent ? (
            <div className="space-y-6">
              <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
                <div className="flex justify-center mb-4">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
                    <Check className="h-8 w-8 text-green-600" />
                  </div>
                </div>
                <h3 className="text-lg font-semibold text-green-900 mb-2">Email Sent!</h3>
                <p className="text-sm text-green-700">
                  We've sent a password reset link to <strong>{email}</strong>
                </p>
                <p className="text-xs text-green-600 mt-2">
                  Please check your inbox and spam folder
                </p>
              </div>

              <div className="text-sm text-gray-600 text-center">
                Didn't receive the email?
                <button
                  onClick={() => setSent(false)}
                  className="ml-1 text-blue-600 hover:text-blue-700 font-medium"
                >
                  Try again
                </button>
              </div>

              <Link to="/login">
                <Button variant="outline" className="w-full">
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Back to Login
                </Button>
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label htmlFor="email">Email Address</Label>
                <div className="relative mt-1">
                  <Mail className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    required
                    className="pl-10"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
              </div>

              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? 'Sending...' : 'Send Reset Link'}
              </Button>

              <Link to="/login">
                <Button variant="ghost" className="w-full">
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Back to Login
                </Button>
              </Link>
            </form>
          )}
        </div>
      </div>

      <div className="hidden lg:flex flex-1 bg-gradient-to-br from-blue-600 to-indigo-600 items-center justify-center p-12">
        <div className="text-white max-w-lg">
          <h2 className="text-4xl font-bold mb-6" style={{fontFamily: 'Space Grotesk, sans-serif'}}>
            Secure Password Reset
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            We'll send you a secure link to reset your password and regain access to your account.
          </p>
          <div className="space-y-4">
            <div className="flex items-start">
              <Check className="h-6 w-6 mr-3 flex-shrink-0" />
              <p>Reset link expires in 1 hour</p>
            </div>
            <div className="flex items-start">
              <Check className="h-6 w-6 mr-3 flex-shrink-0" />
              <p>Secure token-based verification</p>
            </div>
            <div className="flex items-start">
              <Check className="h-6 w-6 mr-3 flex-shrink-0" />
              <p>Encrypted password storage</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword;
