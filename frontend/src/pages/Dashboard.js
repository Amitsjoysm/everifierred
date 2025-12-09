import React, { useState, useEffect } from 'react';
import { Mail, Upload, Download, Clock, CheckCircle, XCircle, BarChart, Key, Copy, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { toast } from 'sonner';
import api from '../utils/api';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import ChatAssistant from '../components/ChatAssistant';
import UsageAnalytics from '../components/UsageAnalytics';

const Dashboard = () => {
  const { user, logout, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [singleEmail, setSingleEmail] = useState('');
  const [verifying, setVerifying] = useState(false);
  const [result, setResult] = useState(null);
  const [bulkFile, setBulkFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [jobs, setJobs] = useState([]);
  const [loadingJobs, setLoadingJobs] = useState(true);
  const [apiKeys, setApiKeys] = useState([]);
  const [loadingKeys, setLoadingKeys] = useState(true);
  const [creatingKey, setCreatingKey] = useState(false);

  useEffect(() => {
    fetchJobs();
    fetchApiKeys();
    const interval = setInterval(() => {
      fetchJobs();
      fetchApiKeys();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchJobs = async () => {
    try {
      const response = await api.get('/verify/jobs');
      setJobs(response.data);
    } catch (error) {
      console.error('Error fetching jobs:', error);
    } finally {
      setLoadingJobs(false);
    }
  };

  const fetchApiKeys = async () => {
    try {
      const response = await api.get('/api-keys');
      setApiKeys(response.data || []);
    } catch (error) {
      console.error('Error fetching API keys:', error);
    } finally {
      setLoadingKeys(false);
    }
  };

  const handleCreateApiKey = async () => {
    setCreatingKey(true);
    try {
      const response = await api.post('/api-keys', {
        name: `API Key ${new Date().toLocaleString()}`
      });
      toast.success('API Key created successfully!');
      fetchApiKeys();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create API key');
    } finally {
      setCreatingKey(false);
    }
  };

  const handleCopyApiKey = (key) => {
    navigator.clipboard.writeText(key);
    toast.success('API Key copied to clipboard!');
  };

  const handleDeleteApiKey = async (keyId) => {
    if (!window.confirm('Are you sure you want to delete this API key?')) return;
    
    try {
      await api.delete(`/api-keys/${keyId}`);
      toast.success('API Key deleted successfully!');
      fetchApiKeys();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete API key');
    }
  };

  const handleSingleVerify = async (e) => {
    e.preventDefault();
    setVerifying(true);
    setResult(null);

    try {
      const response = await api.post('/verify/single', { email: singleEmail });
      setResult(response.data);
      toast.success('Email verified successfully!');
      setSingleEmail('');
      // Refresh user data to update credits
      await refreshUser();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Verification failed');
    } finally {
      setVerifying(false);
    }
  };

  const handleBulkUpload = async (e) => {
    e.preventDefault();
    if (!bulkFile) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', bulkFile);

    try {
      const response = await api.post('/verify/bulk', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      toast.success('File uploaded! Verification started.');
      setBulkFile(null);
      fetchJobs();
      // Refresh user data to update credits
      await refreshUser();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = async (jobId) => {
    try {
      const response = await api.get(`/verify/download/${jobId}`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `verification_results_${jobId}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('Results downloaded!');
    } catch (error) {
      toast.error('Download failed');
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Mail className="h-8 w-8 text-blue-600" />
            <span className="text-2xl font-bold text-gray-900">MailGuard</span>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <p className="text-sm text-gray-600">{user?.email}</p>
              <p className="text-xs text-gray-500">
                {user?.credits_used || 0} / {user?.credits_limit || 100} credits used
              </p>
            </div>
            {user?.role !== 'user' && (
              <Button variant="outline" onClick={() => navigate('/admin')} data-testid="admin-panel-btn">
                Admin Panel
              </Button>
            )}
            <Button variant="outline" onClick={logout} data-testid="logout-btn">
              Logout
            </Button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Welcome, {user?.full_name}!</h1>
          <p className="text-gray-600">Verify emails and manage your account</p>
        </div>

        {/* Stats Cards */}
        <div className="grid md:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Credits Left</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {(user?.credits_limit || 100) - (user?.credits_used || 0)}
                  </p>
                </div>
                <BarChart className="h-8 w-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Jobs</p>
                  <p className="text-2xl font-bold text-gray-900">{jobs.length}</p>
                </div>
                <Upload className="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Completed</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {jobs.filter((j) => j.status === 'completed').length}
                  </p>
                </div>
                <CheckCircle className="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Processing</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {jobs.filter((j) => j.status === 'processing' || j.status === 'pending').length}
                  </p>
                </div>
                <Clock className="h-8 w-8 text-yellow-600" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Usage Analytics Widget */}
        <div className="mb-8">
          <UsageAnalytics />
        </div>

        {/* Main Content */}
        <Tabs defaultValue="single" className="space-y-6">
          <TabsList className="grid w-full max-w-3xl grid-cols-3">
            <TabsTrigger value="single" data-testid="single-verify-tab">Single Verification</TabsTrigger>
            <TabsTrigger value="bulk" data-testid="bulk-verify-tab">Bulk Verification</TabsTrigger>
            <TabsTrigger value="api" data-testid="api-access-tab">API & MCP Access</TabsTrigger>
          </TabsList>

          {/* Single Email Verification */}
          <TabsContent value="single">
            <Card>
              <CardHeader>
                <CardTitle>Verify Single Email</CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSingleVerify} className="space-y-4">
                  <div>
                    <Label htmlFor="email">Email Address</Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder="example@domain.com"
                      value={singleEmail}
                      onChange={(e) => setSingleEmail(e.target.value)}
                      required
                      data-testid="single-email-input"
                    />
                  </div>
                  <Button type="submit" disabled={verifying} data-testid="verify-email-btn">
                    {verifying ? 'Verifying...' : 'Verify Email'}
                  </Button>
                </form>

                {result && (
                  <div className="mt-6 p-6 bg-gray-50 rounded-lg" data-testid="verification-result">
                    <h3 className="font-semibold text-lg mb-4">Verification Result</h3>
                    <div className="grid md:grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-gray-600">Email</p>
                        <p className="font-medium">{result.input}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Confidence Score</p>
                        <p className={`text-2xl font-bold ${getScoreColor(result.confidence_score)}`}>
                          {result.confidence_score.toFixed(0)}%
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Status</p>
                        <p className="font-medium capitalize">{result.is_reachable}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Deliverable</p>
                        <p className="font-medium">{result.is_deliverable ? 'Yes' : 'No'}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Disposable</p>
                        <p className="font-medium">{result.is_disposable ? 'Yes' : 'No'}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Domain</p>
                        <p className="font-medium">{result.domain}</p>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Bulk Verification */}
          <TabsContent value="bulk">
            <Card>
              <CardHeader>
                <CardTitle>Bulk Email Verification</CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleBulkUpload} className="space-y-4">
                  <div>
                    <Label htmlFor="file">Upload File (CSV, Excel, or TXT)</Label>
                    <Input
                      id="file"
                      type="file"
                      accept=".csv,.xlsx,.xls,.txt"
                      onChange={(e) => setBulkFile(e.target.files[0])}
                      required
                      data-testid="bulk-file-input"
                    />
                    <p className="text-sm text-gray-500 mt-1">
                      Supported formats: CSV, Excel (.xlsx, .xls), TXT
                    </p>
                  </div>
                  <Button type="submit" disabled={uploading || !bulkFile} data-testid="upload-bulk-btn">
                    {uploading ? 'Uploading...' : 'Upload & Verify'}
                  </Button>
                </form>

                {/* Jobs List */}
                <div className="mt-8">
                  <h3 className="font-semibold text-lg mb-4">Verification Jobs</h3>
                  {loadingJobs ? (
                    <p className="text-gray-500">Loading jobs...</p>
                  ) : jobs.length === 0 ? (
                    <p className="text-gray-500">No jobs yet</p>
                  ) : (
                    <div className="space-y-3">
                      {jobs.map((job) => (
                        <div key={job.id} className="p-4 bg-white border border-gray-200 rounded-lg" data-testid="job-item">
                          <div className="flex items-center justify-between mb-2">
                            <div>
                              <p className="font-medium">Job ID: {job.id.substring(0, 8)}...</p>
                              <p className="text-sm text-gray-600">
                                {job.total_emails} emails • {new Date(job.created_at).toLocaleString()}
                              </p>
                            </div>
                            <div className="flex items-center space-x-2">
                              {job.status === 'completed' ? (
                                <>
                                  <CheckCircle className="h-5 w-5 text-green-600" />
                                  <Button
                                    size="sm"
                                    onClick={() => handleDownload(job.id)}
                                    data-testid="download-results-btn"
                                  >
                                    <Download className="h-4 w-4 mr-1" />
                                    Download
                                  </Button>
                                </>
                              ) : job.status === 'failed' ? (
                                <XCircle className="h-5 w-5 text-red-600" />
                              ) : (
                                <Clock className="h-5 w-5 text-yellow-600" />
                              )}
                            </div>
                          </div>
                          {(job.status === 'processing' || job.status === 'pending') && (
                            <div>
                              <div className="flex justify-between text-sm text-gray-600 mb-1">
                                <span>Progress</span>
                                <span>{job.processed_emails} / {job.total_emails}</span>
                              </div>
                              <Progress value={(job.processed_emails / job.total_emails) * 100} />
                            </div>
                          )}
                          {job.status === 'completed' && (
                            <div className="flex space-x-4 text-sm mt-2">
                              <span className="text-green-600">✓ {job.successful} successful</span>
                              <span className="text-red-600">✗ {job.failed} failed</span>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* API & MCP Access Tab */}
          <TabsContent value="api">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>API & MCP Access</CardTitle>
                  <Button onClick={handleCreateApiKey} disabled={creatingKey}>
                    <Plus className="h-4 w-4 mr-2" />
                    {creatingKey ? 'Creating...' : 'Create API Key'}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {/* API Keys List */}
                  <div>
                    <h3 className="font-semibold text-lg mb-4">Your API Keys</h3>
                    {loadingKeys ? (
                      <p className="text-gray-500">Loading API keys...</p>
                    ) : apiKeys.length === 0 ? (
                      <div className="text-center py-8 bg-gray-50 rounded-lg">
                        <Key className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                        <p className="text-gray-600 mb-2">No API keys yet</p>
                        <p className="text-sm text-gray-500">Create an API key to access the API and MCP endpoints</p>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {apiKeys.map((apiKey) => (
                          <div key={apiKey.id} className="p-4 bg-white border border-gray-200 rounded-lg">
                            <div className="flex items-center justify-between">
                              <div className="flex-1 mr-4">
                                <p className="font-medium mb-1">{apiKey.name || 'Unnamed Key'}</p>
                                <div className="flex items-center space-x-2">
                                  <code className="text-sm bg-gray-100 px-3 py-1 rounded font-mono">
                                    {apiKey.key.substring(0, 20)}...{apiKey.key.substring(apiKey.key.length - 4)}
                                  </code>
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => handleCopyApiKey(apiKey.key)}
                                  >
                                    <Copy className="h-4 w-4" />
                                  </Button>
                                </div>
                                <div className="flex items-center space-x-4 mt-2 text-xs text-gray-600">
                                  <span>Calls: {apiKey.calls_count || 0}</span>
                                  <span>Created: {new Date(apiKey.created_at).toLocaleDateString()}</span>
                                  {apiKey.last_used && (
                                    <span>Last used: {new Date(apiKey.last_used).toLocaleDateString()}</span>
                                  )}
                                </div>
                              </div>
                              <Button
                                size="sm"
                                variant="destructive"
                                onClick={() => handleDeleteApiKey(apiKey.id)}
                              >
                                Delete
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* API Documentation */}
                  <div className="mt-8 p-6 bg-blue-50 rounded-lg">
                    <h3 className="font-semibold text-lg mb-4">API Endpoints</h3>
                    <div className="space-y-4 text-sm">
                      <div>
                        <p className="font-semibold text-gray-900 mb-1">Single Email Verification</p>
                        <code className="block bg-white p-3 rounded text-xs overflow-x-auto">
                          POST {process.env.REACT_APP_BACKEND_URL}/api/external/verify<br/>
                          Headers: X-API-Key: YOUR_API_KEY<br/>
                          Body: &#123;"email": "test@example.com"&#125;
                        </code>
                      </div>

                      <div>
                        <p className="font-semibold text-gray-900 mb-1">MCP Endpoint (for LLMs)</p>
                        <code className="block bg-white p-3 rounded text-xs overflow-x-auto">
                          POST {process.env.REACT_APP_BACKEND_URL}/api/mcp/verify<br/>
                          Headers: X-API-Key: YOUR_API_KEY<br/>
                          Body: &#123;"email": "test@example.com"&#125;
                        </code>
                      </div>

                      <div>
                        <p className="font-semibold text-gray-900 mb-1">MCP Bulk Verification</p>
                        <code className="block bg-white p-3 rounded text-xs overflow-x-auto">
                          POST {process.env.REACT_APP_BACKEND_URL}/api/mcp/verify-bulk<br/>
                          Headers: X-API-Key: YOUR_API_KEY<br/>
                          Body: &#123;"emails": ["test1@example.com", "test2@example.com"]&#125;
                        </code>
                      </div>

                      <div>
                        <p className="font-semibold text-gray-900 mb-1">MCP Capabilities</p>
                        <code className="block bg-white p-3 rounded text-xs overflow-x-auto">
                          GET {process.env.REACT_APP_BACKEND_URL}/api/mcp/capabilities
                        </code>
                      </div>

                      <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded">
                        <p className="text-sm text-yellow-900">
                          <strong>Note:</strong> Keep your API keys secure and never share them publicly. 
                          Each verification consumes 1 credit from your plan limit.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

        </Tabs>
      </div>

      {/* Chat Assistant */}
      <ChatAssistant />
    </div>
  );
};

export default Dashboard;
