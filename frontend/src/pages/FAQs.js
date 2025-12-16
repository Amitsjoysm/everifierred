import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronDown, ChevronUp } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { useAuth } from '../context/AuthContext';
import SEO from '../components/SEO';
import MobileMenu from '../components/MobileMenu';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const FAQs = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [faqs, setFaqs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('all');

  const mobileMenuLinks = [
    { to: '/', label: 'Home' },
    { to: '/pricing', label: 'Pricing' },
    { to: '/blog', label: 'Blog' },
  ];

  useEffect(() => {
    fetchFAQs();
  }, []);

  const fetchFAQs = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/content/faqs`);
      setFaqs(response.data);
    } catch (error) {
      console.error('Error fetching FAQs:', error);
      toast.error('Failed to load FAQs');
    } finally {
      setLoading(false);
    }
  };

  const categories = ['all', ...new Set(faqs.map((faq) => faq.category))];
  const filteredFaqs =
    selectedCategory === 'all' ? faqs : faqs.filter((faq) => faq.category === selectedCategory);

  const toggleFAQ = (id) => {
    setExpandedId(expandedId === id ? null : id);
  };

  // JSON-LD Structured Data
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: faqs.map((faq) => ({
      '@type': 'Question',
      name: faq.question,
      acceptedAnswer: {
        '@type': 'Answer',
        text: faq.answer,
      },
    })),
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <SEO
        title="FAQs - Email Verification Questions Answered | MailGuard"
        description="Frequently asked questions about MailGuard email verification service. Find answers about pricing, features, API integration, bulk verification, SMTP validation, and more."
        keywords="email verification FAQ, MailGuard help, email validation questions, API documentation, pricing information, bulk verification guide, SMTP verification, email deliverability"
        canonicalUrl="https://page-structure-fix.preview.emergentagent.com/faqs"
        structuredData={jsonLd}
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
            <div className="hidden md:flex items-center gap-6">
              <span
                className="text-gray-700 hover:text-gray-900 cursor-pointer transition-colors"
                onClick={() => navigate('/')}
              >
                Home
              </span>
              <span
                className="text-gray-700 hover:text-gray-900 cursor-pointer transition-colors"
                onClick={() => navigate('/pricing')}
              >
                Pricing
              </span>
              <span
                className="text-gray-700 hover:text-gray-900 cursor-pointer transition-colors"
                onClick={() => navigate('/blog')}
              >
                Blog
              </span>
              {isAuthenticated ? (
                <button
                  onClick={() => navigate('/dashboard')}
                  className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
                >
                  Dashboard
                </button>
              ) : (
                <button
                  onClick={() => navigate('/login')}
                  className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
                >
                  Login
                </button>
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
        {/* Hero Section */}
        <header className="bg-gradient-to-r from-blue-600 to-purple-600 text-white py-16 sm:py-20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h1 id="faq-heading" className="text-4xl sm:text-5xl font-bold mb-4">Frequently Asked Questions</h1>
            <p className="text-lg sm:text-xl text-blue-100 max-w-2xl mx-auto">
              Find answers to common questions about email verification and our services
            </p>
          </div>
        </header>

        {/* FAQ Content */}
        <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16" aria-labelledby="faq-content-heading">
          <h2 id="faq-content-heading" className="sr-only">FAQ Content</h2>
          {/* Category Filter */}
          <div className="mb-8 flex flex-wrap gap-2" role="group" aria-label="FAQ category filter">
            {categories.map((category) => (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`px-3 sm:px-4 py-2 rounded-lg font-medium transition text-sm sm:text-base ${
                  selectedCategory === category
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-100'
                }`}
                aria-pressed={selectedCategory === category}
              >
                {category.charAt(0).toUpperCase() + category.slice(1)}
              </button>
            ))}
          </div>

          {/* FAQ Items */}
          <div className="space-y-4">
            {filteredFaqs.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-lg shadow-md">
                <p className="text-gray-600 text-base sm:text-lg">No FAQs found in this category</p>
              </div>
            ) : (
              filteredFaqs.map((faq) => (
                <article
                  key={faq.id}
                  className="bg-white rounded-lg shadow-md overflow-hidden transition-shadow hover:shadow-lg"
                >
                  <button
                    onClick={() => toggleFAQ(faq.id)}
                    className="w-full flex justify-between items-center p-4 sm:p-6 text-left"
                    aria-expanded={expandedId === faq.id}
                    aria-controls={`faq-answer-${faq.id}`}
                  >
                    <h2 className="text-base sm:text-lg font-semibold text-gray-900 pr-4">{faq.question}</h2>
                    {expandedId === faq.id ? (
                      <ChevronUp className="w-5 h-5 text-blue-600 flex-shrink-0" aria-hidden="true" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-gray-400 flex-shrink-0" aria-hidden="true" />
                    )}
                  </button>

                  {expandedId === faq.id && (
                    <div id={`faq-answer-${faq.id}`} className="px-4 sm:px-6 pb-4 sm:pb-6">
                      <div className="pt-4 border-t border-gray-200">
                        <p className="text-sm sm:text-base text-gray-600 leading-relaxed">{faq.answer}</p>
                      </div>
                    </div>
                  )}
                </article>
              ))
            )}
          </div>

          {/* Contact CTA */}
          <aside className="mt-12 sm:mt-16 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-6 sm:p-8 text-white text-center">
            <h2 className="text-2xl sm:text-3xl font-bold mb-4">Still have questions?</h2>
            <p className="text-sm sm:text-base text-blue-100 mb-6">We're here to help! Contact our support team for assistance.</p>
            <button 
              className="px-6 py-3 bg-white text-blue-600 rounded-lg font-semibold hover:bg-gray-100 transition-colors text-sm sm:text-base"
              onClick={() => navigate('/login')}
            >
              Contact Support
            </button>
          </aside>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12 mt-24" role="contentinfo">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-8">
            <div>
              <h2 className="text-lg sm:text-xl font-bold mb-4">MailGuard</h2>
              <p className="text-sm sm:text-base text-gray-400">Professional email verification for businesses</p>
            </div>
            <nav aria-label="Product navigation">
              <h3 className="text-base font-semibold mb-4">Product</h3>
              <ul className="space-y-2 text-sm text-gray-400">
                <li className="cursor-pointer hover:text-white transition-colors" onClick={() => navigate('/')}>
                  Features
                </li>
                <li className="cursor-pointer hover:text-white transition-colors" onClick={() => navigate('/pricing')}>
                  Pricing
                </li>
                <li className="cursor-pointer hover:text-white transition-colors" onClick={() => navigate('/blog')}>
                  Blog
                </li>
              </ul>
            </nav>
            <nav aria-label="Support navigation">
              <h3 className="text-base font-semibold mb-4">Support</h3>
              <ul className="space-y-2 text-sm text-gray-400">
                <li className="cursor-pointer hover:text-white transition-colors" onClick={() => navigate('/faqs')}>
                  FAQs
                </li>
                <li className="cursor-pointer hover:text-white transition-colors">Contact</li>
              </ul>
            </nav>
            <nav aria-label="Legal navigation">
              <h3 className="text-base font-semibold mb-4">Legal</h3>
              <ul className="space-y-2 text-sm text-gray-400">
                <li className="cursor-pointer hover:text-white transition-colors">Privacy Policy</li>
                <li className="cursor-pointer hover:text-white transition-colors">Terms of Service</li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-sm text-gray-400">
            <p>&copy; 2025 MailGuard. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default FAQs;
