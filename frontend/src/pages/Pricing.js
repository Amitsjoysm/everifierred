import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, Zap, TrendingDown } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { useAuth } from '../context/AuthContext';
import SEO from '../components/SEO';
import MobileMenu from '../components/MobileMenu';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const Pricing = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated, refreshUser } = useAuth();
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [billingCycle, setBillingCycle] = useState('monthly'); // 'monthly' or 'yearly'

  const mobileMenuLinks = [
    { to: '/', label: 'Home' },
    { to: '/blog', label: 'Blog' },
    { to: '/faqs', label: 'FAQs' },
  ];

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

  const getPlanPrice = (plan) => {
    return billingCycle === 'yearly' ? plan.yearly_price : plan.price;
  };

  const getOriginalPrice = (plan) => {
    return billingCycle === 'yearly' ? plan.yearly_original_price : plan.original_price;
  };

  const getDiscountPercentage = (plan) => {
    return billingCycle === 'yearly' ? plan.yearly_discount_percentage : plan.discount_percentage;
  };

  const getSavings = (plan) => {
    const originalPrice = getOriginalPrice(plan);
    const currentPrice = getPlanPrice(plan);
    return originalPrice - currentPrice;
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
      
      // Create subscription
      const response = await axios.post(
        `${API_URL}/api/payments/create-subscription?plan_id=${plan.id}&billing_cycle=${billingCycle}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // Initialize Razorpay Subscription
      const options = {
        key: response.data.razorpay_key,
        subscription_id: response.data.subscription_id,
        name: 'MailGuard',
        description: `${plan.name} Plan - ${billingCycle === 'yearly' ? 'Yearly' : 'Monthly'} Subscription`,
        handler: async function (razorpayResponse) {
          try {
            // Verify subscription payment
            const verifyResponse = await axios.post(
              `${API_URL}/api/payments/verify-subscription`,
              {
                razorpay_order_id: razorpayResponse.razorpay_subscription_id, // This is actually subscription_id
                razorpay_payment_id: razorpayResponse.razorpay_payment_id,
                razorpay_signature: razorpayResponse.razorpay_signature,
                plan_id: plan.id,
                billing_cycle: billingCycle
              },
              { headers: { Authorization: `Bearer ${token}` } }
            );
            
            // Refresh user data to show updated plan and credits
            await refreshUser();
            
            toast.success(`🎉 Subscription activated! Welcome to ${plan.name} plan with ${plan.credits_limit} credits ${billingCycle === 'yearly' ? 'per month' : 'per month'}!`);
            navigate('/dashboard');
          } catch (error) {
            console.error('Subscription verification error:', error);
            
            // Show detailed error message
            let errorMsg = 'Unable to verify subscription';
            
            if (error.response?.data?.detail) {
              if (typeof error.response.data.detail === 'string') {
                errorMsg = error.response.data.detail;
              } else if (Array.isArray(error.response.data.detail)) {
                errorMsg = error.response.data.detail
                  .map(err => err.msg || JSON.stringify(err))
                  .join(', ');
              } else if (typeof error.response.data.detail === 'object') {
                errorMsg = JSON.stringify(error.response.data.detail);
              }
            } else if (error.response?.data?.message) {
              errorMsg = error.response.data.message;
            } else if (error.message) {
              errorMsg = error.message;
            }
            
            toast.error(errorMsg);
            
            // If verification failed, redirect to pricing page to retry
            setTimeout(() => {
              navigate('/pricing');
            }, 2000);
          }
        },
        prefill: {
          name: user?.full_name,
          email: user?.email,
        },
        theme: {
          color: '#3b82f6',
        },
        modal: {
          ondismiss: function () {
            toast.info('Subscription cancelled. You can try again anytime.');
          }
        }
      };

      const rzp = new window.Razorpay(options);
      rzp.on('payment.failed', function (response) {
        toast.error('Payment failed: ' + response.error.description);
        // Redirect back to pricing page after a delay to allow retry
        setTimeout(() => {
          navigate('/pricing');
        }, 2000);
      });
      rzp.open();
    } catch (error) {
      console.error('Error creating subscription:', error);
      let errorMsg = 'Failed to initialize subscription';
      
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
      price: getPlanPrice(plan),
      priceCurrency: 'INR',
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
        description="Flexible pricing plans for email verification. Start free with 100 verifications/month. Affordable paid plans from ₹499/month. No contracts, cancel anytime. Bulk discounts available."
        keywords="email verification pricing, email validation cost, affordable email checker, free email verification, bulk email verification pricing, email verification plans"
        canonicalUrl="https://page-structure-fix.preview.emergentagent.com/pricing"
        structuredData={structuredData}
      />
      
      {/* Navigation */}
      <nav className="bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50" role="navigation" aria-label="Main navigation">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center cursor-pointer" onClick={() => navigate('/')}>
              <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                MailGuard
              </span>
            </div>
            <div className="hidden md:flex items-center gap-4">
              {isAuthenticated ? (
                <button
                  onClick={() => navigate('/dashboard')}
                  className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
                >
                  Dashboard
                </button>
              ) : (
                <>
                  <button
                    onClick={() => navigate('/login')}
                    className="px-4 py-2 text-gray-700 hover:text-gray-900 transition-colors"
                  >
                    Login
                  </button>
                  <button
                    onClick={() => navigate('/register')}
                    className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
                  >
                    Sign Up
                  </button>
                </>
              )}
            </div>
            
            {/* Mobile Menu */}
            <MobileMenu
              links={mobileMenuLinks}
              isAuthenticated={isAuthenticated}
              onDashboardClick={() => navigate('/dashboard')}
              onLoginClick={() => navigate('/login')}
              onRegisterClick={() => navigate('/register')}
            />
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main>
        {/* Pricing Section */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16 md:py-24" aria-label="Pricing plans">
          <header className="text-center mb-12">
            <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Simple, Transparent Pricing
            </h1>
            <p className="text-base sm:text-lg md:text-xl text-gray-600 max-w-2xl mx-auto mb-8">
              Choose the perfect plan for your email verification needs. All plans include our core features.
            </p>

            {/* Billing Cycle Toggle */}
            <div className="flex items-center justify-center gap-3 sm:gap-4 mb-4" role="group" aria-label="Billing cycle selector">
              <span className={`text-base sm:text-lg font-medium ${billingCycle === 'monthly' ? 'text-gray-900' : 'text-gray-500'}`}>
                Monthly
              </span>
              <button
                onClick={() => setBillingCycle(billingCycle === 'monthly' ? 'yearly' : 'monthly')}
                className={`relative inline-flex h-8 w-16 items-center rounded-full transition-colors ${
                  billingCycle === 'yearly' ? 'bg-green-600' : 'bg-gray-300'
                }`}
                aria-label={`Switch to ${billingCycle === 'monthly' ? 'yearly' : 'monthly'} billing`}
                aria-pressed={billingCycle === 'yearly'}
              >
                <span
                  className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform ${
                    billingCycle === 'yearly' ? 'translate-x-9' : 'translate-x-1'
                  }`}
                />
              </button>
              <span className={`text-base sm:text-lg font-medium ${billingCycle === 'yearly' ? 'text-gray-900' : 'text-gray-500'}`}>
                Yearly
              </span>
            </div>
            
            {/* Savings Badge */}
            {billingCycle === 'yearly' && (
              <div className="inline-flex items-center gap-2 px-3 sm:px-4 py-2 rounded-full bg-green-100 text-green-700 text-xs sm:text-sm font-semibold">
                <TrendingDown className="w-3 h-3 sm:w-4 sm:h-4" aria-hidden="true" />
                Save up to 62% with yearly billing!
              </div>
            )}
          </header>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 lg:gap-8">
          {plans.map((plan, index) => {
            const price = getPlanPrice(plan);
            const originalPrice = getOriginalPrice(plan);
            const discount = getDiscountPercentage(plan);
            const savings = getSavings(plan);
            const monthlyEquivalent = billingCycle === 'yearly' ? (price / 12).toFixed(0) : null;

            return (
              <article
                key={plan.id}
                className={`relative bg-white rounded-2xl shadow-xl overflow-hidden transition-all duration-300 hover:scale-105 ${
                  plan.type === 'professional' ? 'ring-2 ring-blue-600 lg:scale-105' : ''
                }`}
              >
                {plan.type === 'professional' && (
                  <div className="absolute top-0 right-0 bg-gradient-to-r from-blue-600 to-purple-600 text-white px-3 sm:px-4 py-1 text-xs sm:text-sm font-semibold rounded-bl-lg" aria-label="Most popular plan">
                    MOST POPULAR
                  </div>
                )}
                
                {discount > 0 && plan.type !== 'free' && (
                  <div className="absolute top-0 left-0 bg-gradient-to-r from-green-500 to-green-600 text-white px-2 sm:px-3 py-1 text-xs font-bold rounded-br-lg flex items-center gap-1" aria-label={`Save ${discount.toFixed(0)} percent`}>
                    <Zap className="w-3 h-3" aria-hidden="true" />
                    SAVE {discount.toFixed(0)}%
                  </div>
                )}

                <div className="p-6 sm:p-8">
                  <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-2">{plan.name}</h2>
                  
                  <div className="mb-6">
                    {plan.type === 'free' ? (
                      <div>
                        <span className="text-3xl sm:text-4xl font-bold text-gray-900">Free</span>
                        <p className="text-sm text-gray-500 mt-1">Forever</p>
                      </div>
                    ) : (
                      <div>
                        {/* Show original price crossed out */}
                        {originalPrice && discount > 0 && (
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-lg sm:text-xl text-gray-400 line-through">
                              ₹{originalPrice.toLocaleString()}
                            </span>
                          </div>
                        )}
                        
                        {/* Current price */}
                        <div className="flex items-baseline gap-1">
                          <span className="text-3xl sm:text-4xl font-bold text-gray-900">
                            ₹{price.toLocaleString()}
                          </span>
                          <span className="text-sm sm:text-base text-gray-600">
                            /{billingCycle === 'yearly' ? 'year' : 'month'}
                          </span>
                        </div>
                        
                        {/* Yearly monthly equivalent */}
                        {billingCycle === 'yearly' && (
                          <p className="text-xs sm:text-sm text-green-600 font-semibold mt-1">
                            ₹{monthlyEquivalent}/month effective
                          </p>
                        )}
                        
                        {/* Savings highlight */}
                        {savings > 0 && (
                          <div className="mt-2 inline-flex items-center gap-1 px-2 sm:px-3 py-1 rounded-full bg-green-50 text-green-700 text-xs sm:text-sm font-semibold">
                            <TrendingDown className="w-3 h-3 sm:w-4 sm:h-4" aria-hidden="true" />
                            Save ₹{savings.toLocaleString()}
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  <p className="text-sm sm:text-base text-gray-600 mb-6">
                    {plan.credits_limit === -1
                      ? 'Unlimited verifications'
                      : `${plan.credits_limit.toLocaleString()} verifications/month`}
                  </p>
                  
                  <button
                    onClick={() => handleSelectPlan(plan)}
                    className={`w-full py-3 px-4 sm:px-6 rounded-lg text-sm sm:text-base font-semibold transition-all duration-200 ${
                      plan.type === 'professional'
                        ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-700 hover:to-purple-700 shadow-lg hover:shadow-xl'
                        : plan.type === 'free'
                        ? 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                        : 'bg-blue-600 text-white hover:bg-blue-700'
                    }`}
                    aria-label={`Select ${plan.name} plan`}
                  >
                    {plan.type === 'free' ? 'Get Started' : `Subscribe ${billingCycle === 'yearly' ? 'Yearly' : 'Monthly'}`}
                  </button>

                  <div className="mt-6 sm:mt-8 space-y-3 sm:space-y-4">
                    <h3 className="text-sm sm:text-base font-semibold text-gray-900">Features:</h3>
                    {plan.features.map((feature, idx) => (
                      <div key={idx} className="flex items-start gap-2 sm:gap-3">
                        <Check className="w-4 h-4 sm:w-5 sm:h-5 text-green-500 flex-shrink-0 mt-0.5" aria-hidden="true" />
                        <span className="text-xs sm:text-sm text-gray-600">{feature}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </article>
            );
          })}
          </div>

          {/* Trust Badges */}
          <aside className="mt-12 sm:mt-16 text-center" aria-label="Trust badges">
            <p className="text-sm sm:text-base text-gray-600 mb-6">Trusted by 10,000+ businesses worldwide</p>
            <div className="flex justify-center items-center gap-4 sm:gap-6 md:gap-8 flex-wrap">
              <div className="flex items-center gap-2 text-gray-700">
                <Check className="w-4 h-4 sm:w-5 sm:h-5 text-green-500" aria-hidden="true" />
                <span className="text-xs sm:text-sm font-medium">Cancel anytime</span>
              </div>
              <div className="flex items-center gap-2 text-gray-700">
                <Check className="w-4 h-4 sm:w-5 sm:h-5 text-green-500" aria-hidden="true" />
                <span className="text-xs sm:text-sm font-medium">No hidden fees</span>
              </div>
              <div className="flex items-center gap-2 text-gray-700">
                <Check className="w-4 h-4 sm:w-5 sm:h-5 text-green-500" aria-hidden="true" />
                <span className="text-xs sm:text-sm font-medium">99.9% uptime</span>
              </div>
              <div className="flex items-center gap-2 text-gray-700">
                <Check className="w-4 h-4 sm:w-5 sm:h-5 text-green-500" aria-hidden="true" />
                <span className="text-xs sm:text-sm font-medium">24/7 support</span>
              </div>
            </div>
          </aside>
        </section>

        {/* FAQ Section */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-16 sm:pb-24" aria-label="Frequently asked questions">
          <h2 className="text-2xl sm:text-3xl font-bold text-center text-gray-900 mb-8 sm:mb-12">
            Frequently Asked Questions
          </h2>
          <div className="max-w-3xl mx-auto space-y-6">
            <div className="bg-white rounded-lg p-6 shadow-md">
              <h3 className="font-semibold text-lg text-gray-900 mb-2">
                Can I switch plans anytime?
              </h3>
              <p className="text-gray-600">
                Yes! You can upgrade, downgrade, or cancel your subscription at any time. Changes take effect immediately.
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
            <div className="bg-white rounded-lg p-6 shadow-md">
              <h3 className="font-semibold text-lg text-gray-900 mb-2">
                How does the yearly billing work?
              </h3>
              <p className="text-gray-600">
                With yearly billing, you pay for 10 months upfront and get 2 months free, plus an additional 10% discount. Your subscription will automatically renew after one year.
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
