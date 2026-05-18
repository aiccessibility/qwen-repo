'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface AnalyticsData {
  total_audits: number;
  status_breakdown: Record<string, number>;
  average_severity: Record<string, number>;
  period_days: number;
}

interface ViolationTrends {
  dates: string[];
  critical: number[];
  serious: number[];
  moderate: number[];
  minor: number[];
  total: number[];
}

interface ComplianceHistory {
  dates: string[];
  scores: number[];
  average_score: number;
}

interface RealtimeMetrics {
  active_audits_count: number;
  active_audits: Array<{
    id: string;
    url: string;
    status: string;
    progress: number;
    created_at: string;
  }>;
  queued_count: number;
  recent_completed: Array<{
    id: string;
    url: string;
    violations_count: number;
    completed_at: string | null;
  }>;
}

export default function DashboardPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [trends, setTrends] = useState<ViolationTrends | null>(null);
  const [compliance, setCompliance] = useState<ComplianceHistory | null>(null);
  const [realtime, setRealtime] = useState<RealtimeMetrics | null>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL_EXTERNAL || 'http://localhost:8000/api/v1';

  useEffect(() => {
    fetchDashboardData();
    // Refresh realtime data every 10 seconds
    const interval = setInterval(fetchRealtimeData, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [analyticsRes, trendsRes, complianceRes] = await Promise.all([
        fetch(`${API_URL}/analytics/statistics?days=30`),
        fetch(`${API_URL}/analytics/trends/violations?days=30`),
        fetch(`${API_URL}/analytics/trends/compliance?days=30`),
      ]);

      if (analyticsRes.ok) {
        const data = await analyticsRes.json();
        setAnalytics(data);
      }

      if (trendsRes.ok) {
        const data = await trendsRes.json();
        setTrends(data);
      }

      if (complianceRes.ok) {
        const data = await complianceRes.json();
        setCompliance(data);
      }

      await fetchRealtimeData();
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchRealtimeData = async () => {
    try {
      const res = await fetch(`${API_URL}/analytics/realtime`);
      if (res.ok) {
        const data = await res.json();
        setRealtime(data);
      }
    } catch (error) {
      console.error('Error fetching realtime data:', error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold text-gray-900">Accessibility Dashboard</h1>
            <button
              onClick={() => router.push('/')}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              New Audit
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Total Audits */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500">Total Audits (30 days)</h3>
            <p className="mt-2 text-3xl font-bold text-gray-900">
              {analytics?.total_audits || 0}
            </p>
          </div>

          {/* Active Audits */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500">Active Audits</h3>
            <p className="mt-2 text-3xl font-bold text-blue-600">
              {realtime?.active_audits_count || 0}
            </p>
          </div>

          {/* Queued */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500">In Queue</h3>
            <p className="mt-2 text-3xl font-bold text-yellow-600">
              {realtime?.queued_count || 0}
            </p>
          </div>

          {/* Average Compliance Score */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500">Avg Compliance Score</h3>
            <p className="mt-2 text-3xl font-bold text-green-600">
              {compliance?.average_score.toFixed(1) || 'N/A'}
            </p>
          </div>
        </div>

        {/* Charts Row 1 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Violation Trends Chart */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Violation Trends</h3>
            {trends && trends.dates.length > 0 ? (
              <div className="h-64 flex items-end space-x-2">
                {trends.dates.map((date, idx) => (
                  <div key={date} className="flex-1 flex flex-col items-center">
                    <div className="w-full flex flex-col items-center space-y-1">
                      {trends.critical[idx] > 0 && (
                        <div
                          className="w-full bg-red-500 rounded-t"
                          style={{ height: `${Math.min(trends.critical[idx] * 5, 100)}px` }}
                          title={`Critical: ${trends.critical[idx]}`}
                        ></div>
                      )}
                      {trends.serious[idx] > 0 && (
                        <div
                          className="w-full bg-orange-500"
                          style={{ height: `${Math.min(trends.serious[idx] * 5, 100)}px` }}
                          title={`Serious: ${trends.serious[idx]}`}
                        ></div>
                      )}
                      {trends.moderate[idx] > 0 && (
                        <div
                          className="w-full bg-yellow-500"
                          style={{ height: `${Math.min(trends.moderate[idx] * 5, 100)}px` }}
                          title={`Moderate: ${trends.moderate[idx]}`}
                        ></div>
                      )}
                      {trends.minor[idx] > 0 && (
                        <div
                          className="w-full bg-green-500 rounded-b"
                          style={{ height: `${Math.min(trends.minor[idx] * 5, 100)}px` }}
                          title={`Minor: ${trends.minor[idx]}`}
                        ></div>
                      )}
                    </div>
                    <span className="text-xs text-gray-500 mt-2 rotate-45 origin-top-left">
                      {date.slice(5)}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-12">No violation data available</p>
            )}
            <div className="mt-4 flex justify-center space-x-4 text-sm">
              <span className="flex items-center">
                <span className="w-3 h-3 bg-red-500 rounded mr-2"></span> Critical
              </span>
              <span className="flex items-center">
                <span className="w-3 h-3 bg-orange-500 rounded mr-2"></span> Serious
              </span>
              <span className="flex items-center">
                <span className="w-3 h-3 bg-yellow-500 rounded mr-2"></span> Moderate
              </span>
              <span className="flex items-center">
                <span className="w-3 h-3 bg-green-500 rounded mr-2"></span> Minor
              </span>
            </div>
          </div>

          {/* Compliance Score History */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Compliance Score History</h3>
            {compliance && compliance.scores.length > 0 ? (
              <div className="h-64 flex items-end space-x-2">
                {compliance.scores.map((score, idx) => (
                  <div key={idx} className="flex-1 flex flex-col items-center">
                    <div
                      className={`w-full rounded-t ${
                        score >= 80 ? 'bg-green-500' : score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ height: `${score * 0.64}px` }}
                      title={`Score: ${score.toFixed(1)}`}
                    ></div>
                    <span className="text-xs text-gray-500 mt-2 rotate-45 origin-top-left">
                      {compliance.dates[idx].slice(5, 10)}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-12">No compliance data available</p>
            )}
          </div>
        </div>

        {/* Severity Breakdown */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Average Violations by Severity</h3>
          {analytics?.average_severity ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-red-50 rounded-lg">
                <p className="text-2xl font-bold text-red-600">
                  {analytics.average_severity.critical?.toFixed(1) || 0}
                </p>
                <p className="text-sm text-gray-600">Critical</p>
              </div>
              <div className="text-center p-4 bg-orange-50 rounded-lg">
                <p className="text-2xl font-bold text-orange-600">
                  {analytics.average_severity.serious?.toFixed(1) || 0}
                </p>
                <p className="text-sm text-gray-600">Serious</p>
              </div>
              <div className="text-center p-4 bg-yellow-50 rounded-lg">
                <p className="text-2xl font-bold text-yellow-600">
                  {analytics.average_severity.moderate?.toFixed(1) || 0}
                </p>
                <p className="text-sm text-gray-600">Moderate</p>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <p className="text-2xl font-bold text-green-600">
                  {analytics.average_severity.minor?.toFixed(1) || 0}
                </p>
                <p className="text-sm text-gray-600">Minor</p>
              </div>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No severity data available</p>
          )}
        </div>

        {/* Active Audits Table */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Active Audits</h3>
          {realtime && realtime.active_audits.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead>
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      URL
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Progress
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Started
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {realtime.active_audits.map((audit) => (
                    <tr key={audit.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {audit.url}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          audit.status === 'completed' ? 'bg-green-100 text-green-800' :
                          audit.status === 'scanning' ? 'bg-blue-100 text-blue-800' :
                          audit.status === 'analyzing' ? 'bg-purple-100 text-purple-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {audit.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${audit.progress}%` }}
                          ></div>
                        </div>
                        <span className="text-xs text-gray-500">{audit.progress}%</span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(audit.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No active audits</p>
          )}
        </div>

        {/* Recent Completed */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recently Completed</h3>
          {realtime && realtime.recent_completed.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead>
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      URL
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Violations
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Completed
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {realtime.recent_completed.map((audit) => (
                    <tr key={audit.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {audit.url}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          audit.violations_count === 0 ? 'bg-green-100 text-green-800' :
                          audit.violations_count < 10 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {audit.violations_count} violations
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {audit.completed_at ? new Date(audit.completed_at).toLocaleString() : 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No recent completed audits</p>
          )}
        </div>
      </main>
    </div>
  );
}
