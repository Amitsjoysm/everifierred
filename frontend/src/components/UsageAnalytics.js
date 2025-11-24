import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Minus, AlertCircle, Zap, Target } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const UsageAnalytics = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [recommendation, setRecommendation] = useState(null);

  useEffect(() => {
    fetchAnalytics();
    fetchRecommendation();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API_URL}/api/assistant/usage-analysis`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchRecommendation = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_URL}/api/assistant/recommend-plan`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setRecommendation(response.data);
    } catch (error) {
      // No recommendation available
      setRecommendation(null);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-md p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-1/4"></div>
          <div className="h-20 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (!analytics) return null;

  // Safely extract values with defaults
  const creditsUsed = analytics.credits_used || 0;
  const creditsLimit = analytics.credits_limit || 1;
  const creditsRemaining = analytics.credits_remaining || 0;
  const dailyAverage = analytics.daily_average || 0;
  const monthlyProjection = analytics.monthly_projection || 0;
  const totalVerifications = analytics.total_verifications || 0;
  const weeklyTrend = analytics.weekly_trend || 'stable';

  const usagePercentage = (creditsUsed / creditsLimit) * 100;
  const getTrendIcon = () => {
    switch (weeklyTrend) {
      case 'increasing':
        return <TrendingUp className="w-5 h-5 text-orange-500" />;
      case 'decreasing':
        return <TrendingDown className="w-5 h-5 text-green-500" />;
      default:
        return <Minus className="w-5 h-5 text-gray-500" />;
    }
  };

  const getTrendColor = () => {
    switch (weeklyTrend) {
      case 'increasing':
        return 'text-orange-600';
      case 'decreasing':
        return 'text-green-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <div className="space-y-6">
      {/* Usage Overview Card */}
      <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl shadow-md p-6 border border-blue-100">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Usage Analytics</h3>
          <div className="flex items-center gap-2">
            {getTrendIcon()}
            <span className={`text-sm font-medium ${getTrendColor()}`}>
              {analytics.weekly_trend}
            </span>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex justify-between text-sm mb-2">
            <span className="text-gray-600">Credits Used</span>
            <span className="font-semibold text-gray-900">
              {analytics.credits_used.toLocaleString()} / {analytics.credits_limit.toLocaleString()}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className={`h-3 rounded-full transition-all duration-500 ${
                usagePercentage > 80
                  ? 'bg-gradient-to-r from-red-500 to-orange-500'
                  : usagePercentage > 50
                  ? 'bg-gradient-to-r from-yellow-500 to-orange-500'
                  : 'bg-gradient-to-r from-green-500 to-blue-500'
              }`}
              style={{ width: `${Math.min(usagePercentage, 100)}%` }}
            ></div>
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>{usagePercentage.toFixed(1)}% used</span>
            <span>{analytics.credits_remaining.toLocaleString()} remaining</span>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white rounded-lg p-3 border border-gray-200">
            <div className="flex items-center gap-2 mb-1">
              <Zap className="w-4 h-4 text-blue-600" />
              <span className="text-xs text-gray-600">Daily Avg</span>
            </div>
            <p className="text-lg font-bold text-gray-900">
              {analytics.daily_average.toFixed(1)}
            </p>
          </div>

          <div className="bg-white rounded-lg p-3 border border-gray-200">
            <div className="flex items-center gap-2 mb-1">
              <Target className="w-4 h-4 text-purple-600" />
              <span className="text-xs text-gray-600">Projection</span>
            </div>
            <p className="text-lg font-bold text-gray-900">
              {analytics.monthly_projection.toLocaleString()}
            </p>
          </div>

          <div className="bg-white rounded-lg p-3 border border-gray-200">
            <div className="flex items-center gap-2 mb-1">
              <AlertCircle className="w-4 h-4 text-orange-600" />
              <span className="text-xs text-gray-600">30 Days</span>
            </div>
            <p className="text-lg font-bold text-gray-900">
              {analytics.total_verifications.toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      {/* Recommendation Card */}
      {recommendation && (
        <div className="bg-gradient-to-br from-orange-50 to-yellow-50 rounded-xl shadow-md p-6 border border-orange-200">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-orange-500 rounded-lg">
              <AlertCircle className="w-6 h-6 text-white" />
            </div>
            <div className="flex-1">
              <h4 className="font-semibold text-gray-900 mb-2">Upgrade Recommendation</h4>
              <p className="text-sm text-gray-700 mb-3">{recommendation.reason}</p>
              
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-lg font-bold text-gray-900">{recommendation.plan_name}</p>
                  <p className="text-sm text-gray-600">₹{recommendation.plan_price}/month</p>
                  {recommendation.savings && (
                    <p className="text-xs text-green-600 font-medium mt-1">
                      Save ₹{recommendation.savings.toFixed(2)}/month
                    </p>
                  )}
                </div>
                <button
                  onClick={() => navigate(recommendation.upgrade_url)}
                  className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition font-medium"
                >
                  Upgrade Now
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Insights */}
      {usagePercentage > 80 && !recommendation && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-red-900 mb-1">High Usage Alert</h4>
              <p className="text-sm text-red-700">
                You've used over 80% of your credits. Consider upgrading to avoid service interruption.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UsageAnalytics;
