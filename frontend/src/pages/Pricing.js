import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, X } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { useAuth } from '../context/AuthContext';
import SEO from '../components/SEO';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const Pricing = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated, refreshUser } = useAuth();
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/plans`);
      setPlans(response.data);
    } catch (error) {
      console.error('Error fetching plans:', error);
      toast.error('Failed to load pricing plans');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPlan = async (plan) => {
    if (!isAuthenticated) {
      toast.info('Please login to subscribe');
      navigate('/login');
      return;
    }

    if (plan.type === 'free') {
      toast.info('You are already on the free plan');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_URL}/api/payments/create-order?plan_id=${plan.id}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // Initialize Razorpay
      const options = {
        key: response.data.razorpay_key,
        amount: response.data.amount,
        currency: response.data.currency,
        name: 'MailGuard',
        description: plan.name + ' Plan',
        order_id: response.data.order_id,
        handler: async function (razorpayResponse) {
          try {
            await axios.post(
              `${API_URL}/api/payments/verify`,
              {
                razorpay_order_id: razorpayResponse.razorpay_order_id,
                razorpay_payment_id: razorpayResponse.razorpay_payment_id,
                razorpay_signature: razorpayResponse.razorpay_signature,
                plan_id: plan.id,
              },
              { headers: { Authorization: `Bearer ${token}` } }
            );
            toast.success('Payment successful! Plan upgraded.');
            navigate('/dashboard');
          } catch (error) {
            toast.error('Payment verification failed');
          }
        },
        prefill: {
          name: user?.full_name,
          email: user?.email,
        },
        theme: {
          color: '#3b82f6',
        },
      };

      const rzp = new window.Razorpay(options);
      rzp.on('payment.failed', function (response) {
        toast.error('Payment failed: ' + response.error.description);
      });
      rzp.open();
    } catch (error) {
      console.error('Error creating order:', error);
      let errorMsg = 'Failed to initialize payment';
      
      if (error.response?.data?.detail) {
        if (typeof error.response.data.detail === 'string') {
          errorMsg = error.response.data.detail;
        } else if (Array.isArray(error.response.data.detail)) {
          errorMsg = error.response.data.detail.map(e => e.msg || e).join(', ');
        }
      }
      
      toast.error(errorMsg);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const structuredData = {
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: 'MailGuard Email Verification',
    description: 'Professional email verification service with flexible pricing plans',
    offers: plans.map(plan => ({
      '@type': 'Offer',
      name: plan.name,
      price: plan.price,
      priceCurrency: 'USD',
      description: `${plan.credits_limit} email verifications per month`,
      seller: {
        '@type': 'Organization',
        name: 'MailGuard',
      },
    })),
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <SEO
        title="Pricing Plans - Affordable Email Verification | MailGuard"
        description="Flexible pricing plans for email verification. Start free with 100 verifications/month. Affordable paid plans from $4.99/month. No contracts, cancel anytime. Bulk discounts available."
        keywords="email verification pricing, email validation cost, affordable email checker, free email verification, bulk email verification pricing, email verification plans"
        canonicalUrl="https://payment-debug-14.preview.emergentagent.com/pricing"
        structuredData={structuredData}
      />
      
      {/* Navigation */}
      <nav className="bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center cursor-pointer" onClick={() => navigate('/')}>
              <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                MailGuard
              </span>
            </div>
            <div className="flex items-center gap-4">
              {isAuthenticated ? (
                <button
                  onClick={() => navigate('/dashboard')}
                  className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition"
                >
                  Dashboard
                </button>
              ) : (
                <>
                  <button
                    onClick={() => navigate('/login')}
                    className="px-4 py-2 text-gray-700 hover:text-gray-900"
                  >
                    Login
                  </button>
                  <button
                    onClick={() => navigate('/register')}
                    className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition"
                  >
                    Sign Up
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Pricing Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            Simple, Transparent Pricing
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Choose the perfect plan for your email verification needs. All plans include our core features.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {plans.map((plan, index) => (
            <div
              key={plan.id}
              className={`relative bg-white rounded-2xl shadow-xl overflow-hidden transition-transform hover:scale-105 ${
                plan.type === 'professional' ? 'ring-2 ring-blue-600' : ''
              }`}
            >
              {plan.type === 'professional' && (
                <div className="absolute top-0 right-0 bg-blue-600 text-white px-4 py-1 text-sm font-semibold">
                  POPULAR
                </div>
              )}
              <div className="p-8">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                <div className="mb-6">
                  <span className="text-4xl font-bold text-gray-900">
                    {plan.price === 0 ? 'Free' : `₹${plan.price}`}
                  </span>
                  {plan.price > 0 && <span className="text-gray-600">/month</span>}
                </div>
                <p className="text-gray-600 mb-6">
                  {plan.credits_limit === -1
                    ? 'Unlimited verifications'
                    : `${plan.credits_limit.toLocaleString()} verifications/month`}
                </p>
                <button
                  onClick={() => handleSelectPlan(plan)}
                  className={`w-full py-3 px-6 rounded-lg font-semibold transition ${
                    plan.type === 'professional'
                      ? 'bg-blue-600 text-white hover:bg-blue-700'
                      : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                  }`}
                >
                  {plan.type === 'free' ? 'Get Started' : 'Subscribe Now'}
                </button>

                <div className="mt-8 space-y-4">
                  <p className="font-semibold text-gray-900">Features:</p>
                  {plan.features.map((feature, idx) => (
                    <div key={idx} className="flex items-start gap-3">
                      <Check className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-600">{feature}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* FAQ Section */}
        <div className="mt-24">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            Frequently Asked Questions
          </h2>
          <div className="max-w-3xl mx-auto space-y-6">
            <div className="bg-white rounded-lg p-6 shadow-md">
              <h3 className="font-semibold text-lg text-gray-900 mb-2">
                Can I switch plans anytime?
              </h3>
              <p className="text-gray-600">
                Yes! You can upgrade or downgrade your plan at any time. Changes take effect immediately.
              </p>
            </div>
            <div className="bg-white rounded-lg p-6 shadow-md">
              <h3 className="font-semibold text-lg text-gray-900 mb-2">
                What payment methods do you accept?
              </h3>
              <p className="text-gray-600">
                We accept all major credit cards, debit cards, UPI, and net banking through Razorpay.
              </p>
            </div>
            <div className="bg-white rounded-lg p-6 shadow-md">
              <h3 className="font-semibold text-lg text-gray-900 mb-2">
                Do unused credits roll over?
              </h3>
              <p className="text-gray-600">
                Credits reset monthly based on your plan. Consider upgrading to a higher plan if you consistently use all your credits.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12 mt-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <h3 className="text-xl font-bold mb-4">MailGuard</h3>
              <p className="text-gray-400">Professional email verification for businesses</p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-gray-400">
                <li className="cursor-pointer hover:text-white" onClick={() => navigate('/')}>
                  Features
                </li>
                <li className="cursor-pointer hover:text-white" onClick={() => navigate('/pricing')}>
                  Pricing
                </li>
                <li className="cursor-pointer hover:text-white" onClick={() => navigate('/blog')}>
                  Blog
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Support</h4>
              <ul className="space-y-2 text-gray-400">
                <li className="cursor-pointer hover:text-white" onClick={() => navigate('/faqs')}>
                  FAQs
                </li>
                <li className="cursor-pointer hover:text-white">Contact</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Legal</h4>
              <ul className="space-y-2 text-gray-400">
                <li className="cursor-pointer hover:text-white">Privacy Policy</li>
                <li className="cursor-pointer hover:text-white">Terms of Service</li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2025 MailGuard. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Pricing;
