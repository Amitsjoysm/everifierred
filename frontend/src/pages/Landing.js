import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { CheckCircle, Shield, Zap, Users, TrendingUp, Mail } from 'lucide-react';
import { Button } from '@/components/ui/button';
import SEO from '../components/SEO';
import MobileMenu from '../components/MobileMenu';

const Landing = () => {
  const navigate = useNavigate();
  
  const mobileMenuLinks = [
    { to: '/pricing', label: 'Pricing' },
    { to: '/blog', label: 'Blog' },
    { to: '/faqs', label: 'FAQs' },
  ];

  const structuredData = {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: 'MailGuard',
    description: 'Professional email verification service for businesses',
    url: 'https://responsive-pages-4.preview.emergentagent.com',
    logo: 'https://responsive-pages-4.preview.emergentagent.com/logo.png',
    sameAs: [
      'https://twitter.com/mailguard',
      'https://linkedin.com/company/mailguard',
    ],
    contactPoint: {
      '@type': 'ContactPoint',
      contactType: 'Customer Support',
      email: 'support@mailguard.com',
    },
    offers: {
      '@type': 'AggregateOffer',
      priceCurrency: 'USD',
      lowPrice: '0',
      highPrice: '79.99',
      offerCount: '4',
    },
  };

  return (
    <div className="min-h-screen">
      <SEO
        title="MailGuard - Professional Email Verification & Validation Service"
        description="Verify email addresses in real-time with MailGuard. Reduce bounce rates by 98%, improve deliverability, and protect your sender reputation. Start free with 100 verifications/month."
        keywords="email verification, email validation, email checker, verify email address, email list cleaning, bulk email verification, email deliverability, bounce rate reduction, SMTP verification, disposable email detection"
        canonicalUrl="https://responsive-pages-4.preview.emergentagent.com"
        structuredData={structuredData}
      />
      {/* Header */}
      <header className="fixed top-0 w-full bg-white/80 backdrop-blur-lg border-b border-gray-200 z-50">
        <nav className="container mx-auto px-6 py-4 flex items-center justify-between" role="navigation" aria-label="Main navigation">
          <div className="flex items-center space-x-2">
            <Mail className="h-8 w-8 text-blue-600" aria-hidden="true" />
            <span className="text-2xl font-bold text-gray-900">MailGuard</span>
          </div>
          <div className="hidden md:flex items-center space-x-8">
            <Link to="/pricing" className="text-gray-600 hover:text-gray-900">Pricing</Link>
            <Link to="/blog" className="text-gray-600 hover:text-gray-900">Blog</Link>
            <Link to="/faqs" className="text-gray-600 hover:text-gray-900">FAQs</Link>
            <Link to="/login">
              <Button variant="ghost" data-testid="login-btn">Login</Button>
            </Link>
            <Link to="/register">
              <Button data-testid="signup-btn">Get Started</Button>
            </Link>
          </div>
          
          {/* Mobile Menu */}
          <MobileMenu
            links={mobileMenuLinks}
            isAuthenticated={false}
            onLoginClick={() => navigate('/login')}
            onRegisterClick={() => navigate('/register')}
          />
        </nav>
      </header>

      {/* Main Content */}
      <main>
        {/* Hero Section */}
        <section className="pt-32 pb-20 px-6 bg-gradient-to-br from-blue-50 via-white to-cyan-50" aria-label="Hero section">
          <div className="container mx-auto text-center max-w-4xl">
            <h1 className="text-4xl sm:text-5xl md:text-7xl font-bold text-gray-900 mb-6" style={{fontFamily: 'Space Grotesk, sans-serif'}}>
              Free Email Verifier for B2B Teams
            </h1>
            <p className="text-lg md:text-xl text-gray-600 mb-8 max-w-2xl mx-auto" style={{fontFamily: 'Inter, sans-serif'}}>
              Clean your email lists, reduce bounce rates, and improve deliverability. 
              Verify emails in bulk with our powerful API and dashboard.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/register">
                <Button size="lg" className="text-lg px-8 py-6 w-full sm:w-auto" data-testid="hero-cta-btn">
                  Start Verifying Free
                </Button>
              </Link>
              <Link to="/pricing">
                <Button size="lg" variant="outline" className="text-lg px-8 py-6 w-full sm:w-auto">
                  View Pricing
                </Button>
              </Link>
            </div>
            <p className="text-sm text-gray-500 mt-4">No credit card required • 100 free verifications</p>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-20 px-6 bg-white" aria-label="Features">
          <div className="container mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-gray-900 mb-4" style={{fontFamily: 'Space Grotesk, sans-serif'}}>
                Everything You Need to Verify Emails
              </h2>
              <p className="text-base sm:text-lg text-gray-600" style={{fontFamily: 'Inter, sans-serif'}}>
                Powerful features for email verification and list cleaning
              </p>
            </div>

            <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-6 sm:gap-8">
              <article className="p-6 sm:p-8 rounded-2xl bg-gradient-to-br from-blue-50 to-cyan-50 border border-blue-100">
                <div className="bg-blue-600 w-12 h-12 rounded-xl flex items-center justify-center mb-4" aria-hidden="true">
                  <CheckCircle className="h-6 w-6 text-white" />
                </div>
                <h3 className="text-lg sm:text-xl font-semibold mb-3 text-gray-900">Real-Time Verification</h3>
                <p className="text-sm sm:text-base text-gray-600">Verify emails instantly with SMTP validation, MX record checks, and disposable email detection</p>
              </article>

              <article className="p-6 sm:p-8 rounded-2xl bg-gradient-to-br from-purple-50 to-pink-50 border border-purple-100">
                <div className="bg-purple-600 w-12 h-12 rounded-xl flex items-center justify-center mb-4" aria-hidden="true">
                  <Zap className="h-6 w-6 text-white" />
                </div>
                <h3 className="text-lg sm:text-xl font-semibold mb-3 text-gray-900">Bulk Upload</h3>
                <p className="text-sm sm:text-base text-gray-600">Upload CSV, Excel, or TXT files and verify thousands of emails in minutes with our async workers</p>
              </article>

              <article className="p-6 sm:p-8 rounded-2xl bg-gradient-to-br from-green-50 to-emerald-50 border border-green-100">
                <div className="bg-green-600 w-12 h-12 rounded-xl flex items-center justify-center mb-4" aria-hidden="true">
                  <Shield className="h-6 w-6 text-white" />
                </div>
                <h3 className="text-lg sm:text-xl font-semibold mb-3 text-gray-900">Confidence Score</h3>
                <p className="text-sm sm:text-base text-gray-600">Get detailed confidence scores (0-100) based on syntax, deliverability, and SMTP validation</p>
              </article>

              <article className="p-6 sm:p-8 rounded-2xl bg-gradient-to-br from-orange-50 to-amber-50 border border-orange-100">
                <div className="bg-orange-600 w-12 h-12 rounded-xl flex items-center justify-center mb-4" aria-hidden="true">
                  <Users className="h-6 w-6 text-white" />
                </div>
                <h3 className="text-lg sm:text-xl font-semibold mb-3 text-gray-900">API Access</h3>
                <p className="text-sm sm:text-base text-gray-600">RESTful API with authentication for seamless integration into your applications</p>
              </article>

              <article className="p-6 sm:p-8 rounded-2xl bg-gradient-to-br from-rose-50 to-red-50 border border-rose-100">
                <div className="bg-rose-600 w-12 h-12 rounded-xl flex items-center justify-center mb-4" aria-hidden="true">
                  <TrendingUp className="h-6 w-6 text-white" />
                </div>
                <h3 className="text-lg sm:text-xl font-semibold mb-3 text-gray-900">Detailed Reports</h3>
                <p className="text-sm sm:text-base text-gray-600">Export results to Excel with all verification fields including MX records and normalized emails</p>
              </article>

              <article className="p-6 sm:p-8 rounded-2xl bg-gradient-to-br from-indigo-50 to-blue-50 border border-indigo-100">
                <div className="bg-indigo-600 w-12 h-12 rounded-xl flex items-center justify-center mb-4" aria-hidden="true">
                  <Mail className="h-6 w-6 text-white" />
                </div>
                <h3 className="text-lg sm:text-xl font-semibold mb-3 text-gray-900">MCP Integration</h3>
                <p className="text-sm sm:text-base text-gray-600">LLM-friendly MCP server endpoint for AI agents and automation tools</p>
              </article>
            </div>
          </div>
        </section>

        {/* Use Cases */}
        <section className="py-20 px-6 bg-gray-50" aria-label="Use cases">
          <div className="container mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-gray-900 mb-4" style={{fontFamily: 'Space Grotesk, sans-serif'}}>
                Perfect for Every Use Case
              </h2>
            </div>

            <div className="grid sm:grid-cols-2 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
              {[
                'Cold Email Outreach',
                'Shopify Store Owners',
                'Real Estate Leads',
                'B2B SaaS Companies',
                'Recruitment Agencies',
                'Email Marketing Teams',
              ].map((useCase) => (
                <article key={useCase} className="p-4 sm:p-6 bg-white rounded-xl border border-gray-200 hover:border-blue-300 hover:shadow-lg transition-all">
                  <CheckCircle className="h-5 w-5 sm:h-6 sm:w-6 text-blue-600 mb-3" aria-hidden="true" />
                  <h3 className="text-base sm:text-lg font-semibold text-gray-900">{useCase}</h3>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-20 px-6 bg-gradient-to-br from-blue-600 to-cyan-600 text-white" aria-label="Call to action">
          <div className="container mx-auto text-center max-w-3xl">
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-6" style={{fontFamily: 'Space Grotesk, sans-serif'}}>
              Start Verifying Emails Today
            </h2>
            <p className="text-lg sm:text-xl mb-8 text-blue-100" style={{fontFamily: 'Inter, sans-serif'}}>
              Join thousands of businesses improving their email deliverability
            </p>
            <Link to="/register">
              <Button size="lg" variant="secondary" className="text-lg px-8 py-6 bg-white text-blue-600 hover:bg-gray-100 w-full sm:w-auto">
                Get Started Free
              </Button>
            </Link>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="py-12 px-6 bg-gray-900 text-gray-400" role="contentinfo">
        <div className="container mx-auto">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <Mail className="h-6 w-6 text-blue-500" aria-hidden="true" />
                <span className="text-xl font-bold text-white">MailGuard</span>
              </div>
              <p className="text-sm">Professional email verification for B2B teams</p>
            </div>
            <div>
              <h2 className="text-white font-semibold mb-4 text-base">Product</h2>
              <ul className="space-y-2 text-sm">
                <li><Link to="/pricing" className="hover:text-white transition-colors">Pricing</Link></li>
                <li><Link to="/blog" className="hover:text-white transition-colors">Blog</Link></li>
              </ul>
            </div>
            <div>
              <h2 className="text-white font-semibold mb-4 text-base">Resources</h2>
              <ul className="space-y-2 text-sm">
                <li><Link to="/blog" className="hover:text-white transition-colors">Blog</Link></li>
                <li><Link to="/faqs" className="hover:text-white transition-colors">FAQs</Link></li>
              </ul>
            </div>
            <div>
              <h2 className="text-white font-semibold mb-4 text-base">Company</h2>
              <ul className="space-y-2 text-sm">
                <li><Link to="/login" className="hover:text-white transition-colors">Login</Link></li>
                <li><Link to="/register" className="hover:text-white transition-colors">Sign Up</Link></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 pt-8 text-center text-sm">
            <p>&copy; 2024 MailGuard. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
