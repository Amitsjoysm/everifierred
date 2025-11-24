import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users,
  CreditCard,
  FileText,
  HelpCircle,
  Settings,
  BarChart3,
  LogOut,
  Plus,
  Edit,
  Trash2,
  Search,
  X,
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { useAuth } from '../context/AuthContext';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const AdminPanel = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('analytics');
  const [loading, setLoading] = useState(true);

  // Analytics
  const [analytics, setAnalytics] = useState(null);

  // Users
  const [users, setUsers] = useState([]);
  const [usersPage, setUsersPage] = useState(1);

  // Plans
  const [plans, setPlans] = useState([]);
  const [showPlanModal, setShowPlanModal] = useState(false);
  const [editingPlan, setEditingPlan] = useState(null);

  // Blogs
  const [blogs, setBlogs] = useState([]);
  const [showBlogModal, setShowBlogModal] = useState(false);
  const [editingBlog, setEditingBlog] = useState(null);

  // FAQs
  const [faqs, setFaqs] = useState([]);
  const [showFaqModal, setShowFaqModal] = useState(false);
  const [editingFaq, setEditingFaq] = useState(null);

  // SEO Settings
  const [seoSettings, setSeoSettings] = useState({
    sitemap_enabled: true,
    robots_txt: '',
    llm_txt: '',
  });

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return { Authorization: `Bearer ${token}` };
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'analytics') {
        await fetchAnalytics();
      } else if (activeTab === 'users') {
        await fetchUsers();
      } else if (activeTab === 'plans') {
        await fetchPlans();
      } else if (activeTab === 'blogs') {
        await fetchBlogs();
      } else if (activeTab === 'faqs') {
        await fetchFaqs();
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const fetchAnalytics = async () => {
    const response = await axios.get(`${API_URL}/api/admin/analytics`, {
      headers: getAuthHeaders(),
    });
    setAnalytics(response.data);
  };

  const fetchUsers = async () => {
    const response = await axios.get(`${API_URL}/api/admin/users?page=${usersPage}&limit=20`, {
      headers: getAuthHeaders(),
    });
    setUsers(response.data || []);
  };

  const fetchPlans = async () => {
    const response = await axios.get(`${API_URL}/api/admin/plans`, {
      headers: getAuthHeaders(),
    });
    setPlans(response.data || []);
  };

  const fetchBlogs = async () => {
    const response = await axios.get(`${API_URL}/api/admin/blogs`, {
      headers: getAuthHeaders(),
    });
    setBlogs(response.data || []);
  };

  const fetchFaqs = async () => {
    const response = await axios.get(`${API_URL}/api/admin/faqs`, {
      headers: getAuthHeaders(),
    });
    setFaqs(response.data || []);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <aside className="w-64 bg-white shadow-lg">
        <div className="p-6">
          <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            MailGuard Admin
          </h2>
          <p className="text-sm text-gray-600 mt-1">{user?.email}</p>
        </div>

        <nav className="mt-6">
          <button
            onClick={() => setActiveTab('analytics')}
            className={`w-full flex items-center gap-3 px-6 py-3 text-left transition ${
              activeTab === 'analytics'
                ? 'bg-blue-50 text-blue-600 border-r-4 border-blue-600'
                : 'text-gray-700 hover:bg-gray-50'
            }`}
          >
            <BarChart3 className="w-5 h-5" />
            <span className="font-medium">Analytics</span>
          </button>

          <button
            onClick={() => setActiveTab('users')}
            className={`w-full flex items-center gap-3 px-6 py-3 text-left transition ${
              activeTab === 'users'
                ? 'bg-blue-50 text-blue-600 border-r-4 border-blue-600'
                : 'text-gray-700 hover:bg-gray-50'
            }`}
          >
            <Users className="w-5 h-5" />
            <span className="font-medium">Users</span>
          </button>

          <button
            onClick={() => setActiveTab('plans')}
            className={`w-full flex items-center gap-3 px-6 py-3 text-left transition ${
              activeTab === 'plans'
                ? 'bg-blue-50 text-blue-600 border-r-4 border-blue-600'
                : 'text-gray-700 hover:bg-gray-50'
            }`}
          >
            <CreditCard className="w-5 h-5" />
            <span className="font-medium">Plans</span>
          </button>

          <button
            onClick={() => setActiveTab('blogs')}
            className={`w-full flex items-center gap-3 px-6 py-3 text-left transition ${
              activeTab === 'blogs'
                ? 'bg-blue-50 text-blue-600 border-r-4 border-blue-600'
                : 'text-gray-700 hover:bg-gray-50'
            }`}
          >
            <FileText className="w-5 h-5" />
            <span className="font-medium">Blogs</span>
          </button>

          <button
            onClick={() => setActiveTab('faqs')}
            className={`w-full flex items-center gap-3 px-6 py-3 text-left transition ${
              activeTab === 'faqs'
                ? 'bg-blue-50 text-blue-600 border-r-4 border-blue-600'
                : 'text-gray-700 hover:bg-gray-50'
            }`}
          >
            <HelpCircle className="w-5 h-5" />
            <span className="font-medium">FAQs</span>
          </button>

          <button
            onClick={() => setActiveTab('seo')}
            className={`w-full flex items-center gap-3 px-6 py-3 text-left transition ${
              activeTab === 'seo'
                ? 'bg-blue-50 text-blue-600 border-r-4 border-blue-600'
                : 'text-gray-700 hover:bg-gray-50'
            }`}
          >
            <Settings className="w-5 h-5" />
            <span className="font-medium">SEO</span>
          </button>
        </nav>

        <div className="absolute bottom-0 w-64 p-6 border-t">
          <button
            onClick={() => navigate('/dashboard')}
            className="w-full mb-2 px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition"
          >
            Back to Dashboard
          </button>
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition"
          >
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <div className="p-8">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <>
              {activeTab === 'analytics' && <AnalyticsTab analytics={analytics} />}
              {activeTab === 'users' && <UsersTab users={users} fetchUsers={fetchUsers} />}
              {activeTab === 'plans' && (
                <PlansTab
                  plans={plans}
                  fetchPlans={fetchPlans}
                  showModal={showPlanModal}
                  setShowModal={setShowPlanModal}
                  editing={editingPlan}
                  setEditing={setEditingPlan}
                  getAuthHeaders={getAuthHeaders}
                />
              )}
              {activeTab === 'blogs' && (
                <BlogsTab
                  blogs={blogs}
                  fetchBlogs={fetchBlogs}
                  showModal={showBlogModal}
                  setShowModal={setShowBlogModal}
                  editing={editingBlog}
                  setEditing={setEditingBlog}
                  getAuthHeaders={getAuthHeaders}
                />
              )}
              {activeTab === 'faqs' && (
                <FAQsTab
                  faqs={faqs}
                  fetchFaqs={fetchFaqs}
                  showModal={showFaqModal}
                  setShowModal={setShowFaqModal}
                  editing={editingFaq}
                  setEditing={setEditingFaq}
                  getAuthHeaders={getAuthHeaders}
                />
              )}
              {activeTab === 'seo' && <SEOTab />}
            </>
          )}
        </div>
      </main>
    </div>
  );
};

// Analytics Tab Component
const AnalyticsTab = ({ analytics }) => {
  if (!analytics) return null;

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Analytics Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Total Users</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">{analytics.total_users}</p>
            </div>
            <Users className="w-12 h-12 text-blue-600" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Active Users</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">{analytics.active_users}</p>
            </div>
            <Users className="w-12 h-12 text-green-600" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Total Verifications</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">{analytics.total_verifications}</p>
            </div>
            <BarChart3 className="w-12 h-12 text-purple-600" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Today's Verifications</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">{analytics.verifications_today}</p>
            </div>
            <BarChart3 className="w-12 h-12 text-orange-600" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Revenue</h3>
          <div className="space-y-4">
            <div>
              <p className="text-gray-600 text-sm">Total Revenue</p>
              <p className="text-2xl font-bold text-gray-900">₹{analytics.revenue_total}</p>
            </div>
            <div>
              <p className="text-gray-600 text-sm">This Month</p>
              <p className="text-2xl font-bold text-green-600">₹{analytics.revenue_month}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Plan Distribution</h3>
          <div className="space-y-3">
            {Object.entries(analytics.plan_distribution).map(([plan, count]) => (
              <div key={plan} className="flex justify-between items-center">
                <span className="text-gray-700 capitalize">{plan}</span>
                <span className="font-semibold text-gray-900">{count} users</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// Users Tab Component
const UsersTab = ({ users, fetchUsers }) => {
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    full_name: '',
    password: '',
    role: 'user',
    plan: 'free',
    credits_limit: 100
  });

  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return { Authorization: `Bearer ${token}` };
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      await axios.post(
        `${API_URL}/api/admin/users`,
        formData,
        { headers: getAuthHeaders() }
      );
      toast.success('User created successfully');
      setShowModal(false);
      setFormData({
        email: '',
        full_name: '',
        password: '',
        role: 'user',
        plan: 'free',
        credits_limit: 100
      });
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create user');
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Users Management</h1>
        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Create User
        </button>
      </div>

      {!users || users.length === 0 ? (
        <div className="bg-white rounded-lg shadow-md p-8 text-center">
          <p className="text-gray-500">No users found</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Plan
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Credits Used
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Role
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {users.map((user) => (
                <tr key={user.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="font-medium text-gray-900">{user.full_name}</div>
                      <div className="text-sm text-gray-500">{user.email}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800 capitalize">
                      {user.plan}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {user.credits_used} / {user.credits_limit}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {user.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-800 capitalize">
                      {user.role}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create User Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Create New User</h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-6 h-6" />
              </button>
            </div>
            <form onSubmit={handleCreateUser} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  value={formData.full_name}
                  onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                <input
                  type="password"
                  required
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData({...formData, role: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                >
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                  <option value="super_admin">Super Admin</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Plan</label>
                <select
                  value={formData.plan}
                  onChange={(e) => setFormData({...formData, plan: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                >
                  <option value="free">Free</option>
                  <option value="starter">Starter</option>
                  <option value="professional">Professional</option>
                  <option value="enterprise">Enterprise</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Credits Limit</label>
                <input
                  type="number"
                  required
                  value={formData.credits_limit}
                  onChange={(e) => setFormData({...formData, credits_limit: parseInt(e.target.value)})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                >
                  Create User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

// Plans Tab Component with full CRUD
const PlansTab = ({ plans, fetchPlans, showModal, setShowModal, editing, setEditing, getAuthHeaders }) => {
  const [formData, setFormData] = useState({
    name: '',
    type: 'free',
    price: 0,
    credits_limit: 100,
    features: [],
    is_active: true
  });

  useEffect(() => {
    if (editing) {
      setFormData({
        name: editing.name || '',
        type: editing.type || 'free',
        price: editing.price || 0,
        credits_limit: editing.credits_limit || 100,
        features: editing.features || [],
        is_active: editing.is_active !== undefined ? editing.is_active : true
      });
    } else {
      setFormData({
        name: '',
        type: 'free',
        price: 0,
        credits_limit: 100,
        features: [],
        is_active: true
      });
    }
  }, [editing]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editing) {
        await axios.patch(
          `${API_URL}/api/admin/plans/${editing.id}`,
          formData,
          { headers: getAuthHeaders() }
        );
        toast.success('Plan updated successfully');
      } else {
        await axios.post(
          `${API_URL}/api/admin/plans`,
          {
            ...formData,
            id: `plan_${Date.now()}`,
            created_at: new Date().toISOString()
          },
          { headers: getAuthHeaders() }
        );
        toast.success('Plan created successfully');
      }
      setShowModal(false);
      setEditing(null);
      fetchPlans();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save plan');
    }
  };

  const handleDelete = async (planId) => {
    if (!window.confirm('Are you sure you want to delete this plan?')) return;
    try {
      await axios.delete(`${API_URL}/api/admin/plans/${planId}`, {
        headers: getAuthHeaders()
      });
      toast.success('Plan deleted successfully');
      fetchPlans();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete plan');
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Plans Management</h1>
        <button
          onClick={() => {
            setEditing(null);
            setShowModal(true);
          }}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Add Plan
        </button>
      </div>

      {!plans || plans.length === 0 ? (
        <div className="bg-white rounded-lg shadow-md p-8 text-center">
          <p className="text-gray-500">No plans found</p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {plans.map((plan) => (
            <div key={plan.id} className="bg-white p-6 rounded-lg shadow-md">
              <h3 className="text-xl font-bold text-gray-900 mb-2">{plan.name}</h3>
              <p className="text-3xl font-bold text-blue-600 mb-4">
                {plan.price === 0 ? 'Free' : `₹${plan.price}`}
              </p>
              <p className="text-gray-600 mb-4">{plan.credits_limit} credits</p>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    setEditing(plan);
                    setShowModal(true);
                  }}
                  className="flex-1 px-3 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition"
                >
                  <Edit className="w-4 h-4 mx-auto" />
                </button>
                <button
                  onClick={() => handleDelete(plan.id)}
                  className="flex-1 px-3 py-2 bg-red-100 text-red-700 rounded hover:bg-red-200 transition"
                >
                  <Trash2 className="w-4 h-4 mx-auto" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create/Edit Plan Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900">
                {editing ? 'Edit Plan' : 'Create New Plan'}
              </h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-6 h-6" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Plan Name</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Plan Type</label>
                <select
                  value={formData.type}
                  onChange={(e) => setFormData({...formData, type: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                >
                  <option value="free">Free</option>
                  <option value="starter">Starter</option>
                  <option value="professional">Professional</option>
                  <option value="enterprise">Enterprise</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Price (₹)</label>
                <input
                  type="number"
                  required
                  value={formData.price}
                  onChange={(e) => setFormData({...formData, price: parseFloat(e.target.value)})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Credits Limit</label>
                <input
                  type="number"
                  required
                  value={formData.credits_limit}
                  onChange={(e) => setFormData({...formData, credits_limit: parseInt(e.target.value)})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                />
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                  className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                />
                <label className="text-sm font-medium text-gray-700">Active</label>
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                >
                  {editing ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

// Blogs Tab Component (stub)
const BlogsTab = ({ blogs }) => {
  if (!blogs || blogs.length === 0) {
    return (
      <div>
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Blog Management</h1>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2">
            <Plus className="w-4 h-4" />
            New Blog
          </button>
        </div>
        <div className="bg-white rounded-lg shadow-md p-8 text-center">
          <p className="text-gray-500">No blogs found</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Blog Management</h1>
        <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2">
          <Plus className="w-4 h-4" />
          New Blog
        </button>
      </div>

      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Title
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Author
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {blogs.map((blog) => (
              <tr key={blog.id}>
                <td className="px-6 py-4">
                  <div className="font-medium text-gray-900">{blog.title}</div>
                  <div className="text-sm text-gray-500">{blog.slug}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{blog.author}</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={`px-2 py-1 text-xs font-semibold rounded-full ${
                      blog.is_published ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                    }`}
                  >
                    {blog.is_published ? 'Published' : 'Draft'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <div className="flex gap-2">
                    <button className="text-blue-600 hover:text-blue-700">
                      <Edit className="w-4 h-4" />
                    </button>
                    <button className="text-red-600 hover:text-red-700">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// FAQs Tab Component (stub)
const FAQsTab = ({ faqs }) => {
  if (!faqs || faqs.length === 0) {
    return (
      <div>
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">FAQ Management</h1>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2">
            <Plus className="w-4 h-4" />
            New FAQ
          </button>
        </div>
        <div className="bg-white rounded-lg shadow-md p-8 text-center">
          <p className="text-gray-500">No FAQs found</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">FAQ Management</h1>
        <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2">
          <Plus className="w-4 h-4" />
          New FAQ
        </button>
      </div>

      <div className="space-y-4">
        {faqs.map((faq) => (
          <div key={faq.id} className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex justify-between items-start mb-2">
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{faq.question}</h3>
                <p className="text-gray-600">{faq.answer}</p>
                <div className="mt-2">
                  <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">{faq.category}</span>
                </div>
              </div>
              <div className="flex gap-2 ml-4">
                <button className="p-2 text-blue-600 hover:bg-blue-50 rounded">
                  <Edit className="w-4 h-4" />
                </button>
                <button className="p-2 text-red-600 hover:bg-red-50 rounded">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// SEO Tab Component
const SEOTab = () => {
  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">SEO Management</h1>

      <div className="space-y-6">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Sitemap</h3>
          <p className="text-gray-600 mb-4">Your sitemap is automatically generated and available at:</p>
          <a
            href="/sitemap.xml"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            {window.location.origin}/sitemap.xml
          </a>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Robots.txt</h3>
          <p className="text-gray-600 mb-4">Configure search engine crawler access:</p>
          <a
            href="/robots.txt"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            {window.location.origin}/robots.txt
          </a>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">LLM.txt</h3>
          <p className="text-gray-600 mb-4">Information for AI crawlers:</p>
          <a
            href="/llm.txt"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            {window.location.origin}/llm.txt
          </a>
        </div>
      </div>
    </div>
  );
};

export default AdminPanel;
