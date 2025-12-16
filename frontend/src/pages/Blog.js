import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Calendar, User, ArrowRight } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { useAuth } from '../context/AuthContext';
import { format } from 'date-fns';
import SEO from '../components/SEO';
import MobileMenu from '../components/MobileMenu';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const Blog = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [blogs, setBlogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  const mobileMenuLinks = [
    { to: '/', label: 'Home' },
    { to: '/pricing', label: 'Pricing' },
    { to: '/faqs', label: 'FAQs' },
  ];

  useEffect(() => {
    fetchBlogs();
  }, []);

  const fetchBlogs = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/content/blogs`);
      setBlogs(response.data);
    } catch (error) {
      console.error('Error fetching blogs:', error);
      toast.error('Failed to load blog posts');
    } finally {
      setLoading(false);
    }
  };

  const filteredBlogs = blogs.filter(
    (blog) =>
      blog.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      blog.excerpt.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const structuredData = {
    '@context': 'https://schema.org',
    '@type': 'Blog',
    name: 'MailGuard Email Verification Blog',
    description: 'Expert insights and guides on email verification best practices',
    url: 'https://page-structure-fix.preview.emergentagent.com/blog',
    publisher: {
      '@type': 'Organization',
      name: 'MailGuard',
      logo: {
        '@type': 'ImageObject',
        url: 'https://page-structure-fix.preview.emergentagent.com/logo.png',
      },
    },
    blogPost: blogs.map(blog => ({
      '@type': 'BlogPosting',
      headline: blog.title,
      description: blog.excerpt,
      url: `https://page-structure-fix.preview.emergentagent.com/blog/${blog.slug}`,
      datePublished: blog.published_at,
      author: {
        '@type': 'Person',
        name: blog.author,
      },
    })),
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <SEO
        title="Email Verification Blog - Expert Insights & Best Practices"
        description="Expert insights, guides, and best practices for email verification and deliverability. Learn about email validation, bounce reduction, sender reputation, and cold email outreach."
        keywords="email verification blog, email validation guide, deliverability tips, sender reputation, bounce rate reduction, cold email best practices, B2B email finder, email list cleaning"
        canonicalUrl="https://page-structure-fix.preview.emergentagent.com/blog"
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
                onClick={() => navigate('/faqs')}
              >
                FAQs
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
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <h1 id="blog-heading" className="text-4xl sm:text-5xl font-bold mb-4">Email Verification Blog</h1>
            <p className="text-lg sm:text-xl text-blue-100 max-w-2xl">
              Expert insights, guides, and best practices for email verification and deliverability
            </p>
          </div>
        </header>

        {/* Search */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-8" aria-labelledby="search-heading">
          <div className="bg-white rounded-lg shadow-lg p-4">
            <label htmlFor="blog-search" className="sr-only">Search articles</label>
            <input
              id="blog-search"
              type="search"
              placeholder="Search articles..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              aria-label="Search blog articles"
            />
          </div>
        </section>

        {/* Blog Posts */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16" aria-label="Blog posts">
          {filteredBlogs.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-600 text-lg">No blog posts found</p>
            </div>
          ) : (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
              {filteredBlogs.map((blog) => (
                <article
                  key={blog.id}
                  className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-2xl transition-shadow cursor-pointer"
                  onClick={() => navigate(`/blog/${blog.slug}`)}
                >
                  <div className="p-6">
                    <div className="flex flex-wrap items-center gap-3 sm:gap-4 text-xs sm:text-sm text-gray-600 mb-4">
                      <div className="flex items-center gap-1">
                        <Calendar className="w-4 h-4" aria-hidden="true" />
                        <time dateTime={blog.published_at}>
                          {blog.published_at
                            ? format(new Date(blog.published_at), 'MMM dd, yyyy')
                            : 'Draft'}
                        </time>
                      </div>
                      <div className="flex items-center gap-1">
                        <User className="w-4 h-4" aria-hidden="true" />
                        <span>{blog.author}</span>
                      </div>
                    </div>

                    <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-3">{blog.title}</h2>
                    <p className="text-sm sm:text-base text-gray-600 mb-4 line-clamp-3">{blog.excerpt}</p>

                    <div className="flex flex-wrap gap-2 mb-4">
                      {blog.keywords.slice(0, 3).map((keyword, idx) => (
                        <span
                          key={idx}
                          className="px-2 sm:px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs sm:text-sm"
                        >
                          {keyword}
                        </span>
                      ))}
                    </div>

                    <div className="flex items-center text-blue-600 font-semibold text-sm sm:text-base">
                      Read More <ArrowRight className="w-4 h-4 ml-1" aria-hidden="true" />
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
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
            <div>
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
            </div>
            <div>
              <h3 className="text-base font-semibold mb-4">Support</h3>
              <ul className="space-y-2 text-sm text-gray-400">
                <li className="cursor-pointer hover:text-white transition-colors" onClick={() => navigate('/faqs')}>
                  FAQs
                </li>
                <li className="cursor-pointer hover:text-white transition-colors">Contact</li>
              </ul>
            </div>
            <div>
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

export default Blog;
