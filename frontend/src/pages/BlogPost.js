import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Calendar, User, ArrowLeft } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { useAuth } from '../context/AuthContext';
import { format } from 'date-fns';
import ReactMarkdown from 'react-markdown';
import SEO from '../components/SEO';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const BlogPost = () => {
  const navigate = useNavigate();
  const { slug } = useParams();
  const { isAuthenticated } = useAuth();
  const [blog, setBlog] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBlog();
  }, [slug]);

  const fetchBlog = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/content/blogs/${slug}`);
      setBlog(response.data);
    } catch (error) {
      console.error('Error fetching blog:', error);
      toast.error('Blog post not found');
      navigate('/blog');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!blog) {
    return null;
  }

  // JSON-LD Structured Data
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'BlogPosting',
    headline: blog.title,
    description: blog.meta_description,
    image: 'https://app-sync-restart.preview.emergentagent.com/blog-default.png',
    author: {
      '@type': 'Person',
      name: blog.author,
    },
    publisher: {
      '@type': 'Organization',
      name: 'MailGuard',
      logo: {
        '@type': 'ImageObject',
        url: 'https://app-sync-restart.preview.emergentagent.com/logo.png',
      },
    },
    datePublished: blog.published_at,
    dateModified: blog.updated_at,
    keywords: blog.keywords.join(', '),
    articleBody: blog.content,
    mainEntityOfPage: {
      '@type': 'WebPage',
      '@id': `https://app-sync-restart.preview.emergentagent.com/blog/${blog.slug}`,
    },
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <SEO
        title={blog.meta_title || blog.title}
        description={blog.meta_description || blog.excerpt}
        keywords={blog.keywords.join(', ')}
        canonicalUrl={`https://app-sync-restart.preview.emergentagent.com/blog/${blog.slug}`}
        ogType="article"
        author={blog.author}
        structuredData={jsonLd}
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
            <div className="flex items-center gap-6">
              <span
                className="text-gray-700 hover:text-gray-900 cursor-pointer"
                onClick={() => navigate('/')}
              >
                Home
              </span>
              <span
                className="text-gray-700 hover:text-gray-900 cursor-pointer"
                onClick={() => navigate('/pricing')}
              >
                Pricing
              </span>
              <span
                className="text-gray-700 hover:text-gray-900 cursor-pointer"
                onClick={() => navigate('/blog')}
              >
                Blog
              </span>
              <span
                className="text-gray-700 hover:text-gray-900 cursor-pointer"
                onClick={() => navigate('/faqs')}
              >
                FAQs
              </span>
              {isAuthenticated ? (
                <button
                  onClick={() => navigate('/dashboard')}
                  className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition"
                >
                  Dashboard
                </button>
              ) : (
                <button
                  onClick={() => navigate('/login')}
                  className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition"
                >
                  Login
                </button>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Article Content */}
      <article className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <button
          onClick={() => navigate('/blog')}
          className="flex items-center text-blue-600 hover:text-blue-700 mb-8"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Blog
        </button>

        <header className="mb-12">
          <div className="flex items-center gap-4 text-sm text-gray-600 mb-4">
            <div className="flex items-center gap-1">
              <Calendar className="w-4 h-4" />
              <span>
                {blog.published_at
                  ? format(new Date(blog.published_at), 'MMMM dd, yyyy')
                  : 'Draft'}
              </span>
            </div>
            <div className="flex items-center gap-1">
              <User className="w-4 h-4" />
              <span>{blog.author}</span>
            </div>
          </div>

          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">{blog.title}</h1>

          <p className="text-xl text-gray-600 mb-6">{blog.excerpt}</p>

          <div className="flex flex-wrap gap-2">
            {blog.keywords.map((keyword, idx) => (
              <span key={idx} className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
                {keyword}
              </span>
            ))}
          </div>
        </header>

        <div className="prose prose-lg max-w-none text-gray-700 leading-relaxed">
          <ReactMarkdown
            components={{
              h1: ({ node, ...props }) => <h1 className="text-3xl font-bold text-gray-900 mt-8 mb-4" {...props} />,
              h2: ({ node, ...props }) => <h2 className="text-2xl font-bold text-gray-900 mt-6 mb-3" {...props} />,
              h3: ({ node, ...props }) => <h3 className="text-xl font-bold text-gray-900 mt-4 mb-2" {...props} />,
              p: ({ node, ...props }) => <p className="mb-4 leading-relaxed" {...props} />,
              ul: ({ node, ...props }) => <ul className="list-disc pl-6 mb-4 space-y-2" {...props} />,
              ol: ({ node, ...props }) => <ol className="list-decimal pl-6 mb-4 space-y-2" {...props} />,
              li: ({ node, ...props }) => <li className="leading-relaxed" {...props} />,
              a: ({ node, ...props }) => (
                <a className="text-blue-600 hover:text-blue-700 underline" {...props} />
              ),
              code: ({ node, inline, ...props }) =>
                inline ? (
                  <code className="bg-gray-100 px-2 py-1 rounded text-sm" {...props} />
                ) : (
                  <code className="block bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto my-4" {...props} />
                ),
            }}
          >
            {blog.content}
          </ReactMarkdown>
        </div>
      </article>

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

export default BlogPost;
