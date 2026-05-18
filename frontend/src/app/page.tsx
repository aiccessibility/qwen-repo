'use client';

import { useState, useEffect } from 'react';
import { Activity, Shield, FileText, Play, CheckCircle, AlertCircle, Clock, BarChart3 } from 'lucide-react';
import Link from 'next/link';

interface AuditResult {
  audit_id: string;
  status: string;
  progress: number;
  violations_count?: number;
  severity_summary?: { critical: number; serious: number; moderate: number; minor: number };
  report_url?: string;
  error?: string;
}

export default function Home() {
  const [url, setUrl] = useState('');
  const [isAuditing, setIsAuditing] = useState(false);
  const [currentAudit, setCurrentAudit] = useState<AuditResult | null>(null);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL_EXTERNAL || 'http://localhost:8000/api/v1';

  const checkAuditStatus = async (auditId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/accessibility/audit/${auditId}`);
      const data = await response.json();
      
      setCurrentAudit(data);
      
      if (data.status === 'completed' || data.status === 'error') {
        if (pollingInterval) {
          clearInterval(pollingInterval);
          setPollingInterval(null);
        }
        setIsAuditing(false);
      }
    } catch (error) {
      console.error('Error checking audit status:', error);
    }
  };

  const handleStartAudit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;

    setIsAuditing(true);
    setCurrentAudit(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/accessibility/audit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: url.startsWith('http') ? url : `https://${url}`,
          wcag_level: 'AA',
          wcag_version: '2.2',
          include_screenshots: true,
          depth: 1,
        }),
      });

      const data = await response.json();
      console.log('Audit started:', data);
      
      // Start polling for status updates
      const interval = setInterval(() => {
        checkAuditStatus(data.audit_id);
      }, 3000);
      
      setPollingInterval(interval);
      
      // Initial status check
      setTimeout(() => {
        checkAuditStatus(data.audit_id);
      }, 1000);
      
    } catch (error) {
      console.error('Error starting audit:', error);
      alert('Error starting audit. Please try again.');
      setIsAuditing(false);
    }
  };

  useEffect(() => {
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [pollingInterval]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100';
      case 'processing': return 'text-blue-600 bg-blue-100';
      case 'error': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-600';
      case 'serious': return 'text-orange-600';
      case 'moderate': return 'text-yellow-600';
      case 'minor': return 'text-blue-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:to-gray-800">
      {/* Header */}
      <header className="border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Shield className="h-8 w-8 text-primary-600" />
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                Accessibility Platform
              </h1>
            </div>
            <nav className="flex space-x-6">
              <Link href="/dashboard" className="flex items-center text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white">
                <BarChart3 className="h-4 w-4 mr-2" />
                Dashboard
              </Link>
              <a href="#" className="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white">
                Audits
              </a>
              <a href="#" className="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white">
                Monitoring
              </a>
              <a href="/docs" className="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white">
                API Docs
              </a>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-extrabold text-gray-900 dark:text-white mb-4">
            AI-Powered Web Accessibility
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
            Automated WCAG compliance auditing, continuous monitoring, and intelligent remediation 
            powered by multi-agent AI systems.
          </p>
        </div>

        {/* Audit Form */}
        <div className="max-w-3xl mx-auto mb-16">
          <form onSubmit={handleStartAudit} className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
            <label htmlFor="url" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Enter URL to Audit
            </label>
            <div className="flex gap-4">
              <input
                type="text"
                id="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="example.com"
                className="flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                required
                disabled={isAuditing}
              />
              <button
                type="submit"
                disabled={isAuditing || !url}
                className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                <Play className="h-5 w-5" />
                {isAuditing ? 'Auditing...' : 'Start Audit'}
              </button>
            </div>
          </form>
        </div>

        {/* Real-time Status */}
        {currentAudit && (
          <div className="max-w-3xl mx-auto mb-16">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Audit Status
                </h3>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(currentAudit.status)}`}>
                  {currentAudit.status.toUpperCase()}
                </span>
              </div>

              {/* Progress Bar */}
              <div className="mb-6">
                <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-2">
                  <span>Progress</span>
                  <span>{currentAudit.progress}%</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                  <div 
                    className="bg-primary-600 h-3 rounded-full transition-all duration-500"
                    style={{ width: `${currentAudit.progress}%` }}
                  />
                </div>
              </div>

              {/* Status Details */}
              {currentAudit.violations_count !== undefined && currentAudit.status === 'completed' && (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-gray-700 dark:text-gray-300">
                    <AlertCircle className="h-5 w-5" />
                    <span className="font-medium">Violations Found: {currentAudit.violations_count}</span>
                  </div>

                  {currentAudit.severity_summary && (
                    <div className="grid grid-cols-4 gap-4">
                      {Object.entries(currentAudit.severity_summary).map(([severity, count]) => (
                        <div key={severity} className="text-center">
                          <div className={`text-2xl font-bold ${getSeverityColor(severity)}`}>
                            {count}
                          </div>
                          <div className="text-sm text-gray-600 dark:text-gray-400 capitalize">
                            {severity}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {currentAudit.report_url && (
                    <div className="flex gap-4 mt-6">
                      <a
                        href={`${API_BASE_URL}/accessibility/audit/${currentAudit.audit_id}/report?format=html`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-center"
                      >
                        <FileText className="h-5 w-5 inline mr-2" />
                        View HTML Report
                      </a>
                      <a
                        href={`${API_BASE_URL}/accessibility/audit/${currentAudit.audit_id}/report?format=pdf`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-center"
                      >
                        <FileText className="h-5 w-5 inline mr-2" />
                        Download PDF
                      </a>
                    </div>
                  )}
                </div>
              )}

              {currentAudit.status === 'processing' && (
                <div className="flex items-center gap-2 text-blue-600">
                  <Clock className="h-5 w-5 animate-spin" />
                  <span>Analyzing accessibility issues...</span>
                </div>
              )}

              {currentAudit.error && (
                <div className="mt-4 p-4 bg-red-100 dark:bg-red-900 rounded-lg">
                  <p className="text-red-600 dark:text-red-300">{currentAudit.error}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-8">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <Activity className="h-12 w-12 text-primary-600 mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              Automated Auditing
            </h3>
            <p className="text-gray-600 dark:text-gray-300">
              AI-powered scanning for WCAG 2.1/2.2 compliance with detailed violation reports and fix recommendations.
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <Shield className="h-12 w-12 text-primary-600 mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              Continuous Monitoring
            </h3>
            <p className="text-gray-600 dark:text-gray-300">
              Autonomous agents track accessibility over time and alert you to regressions before users notice.
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <FileText className="h-12 w-12 text-primary-600 mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              Comprehensive Reports
            </h3>
            <p className="text-gray-600 dark:text-gray-300">
              Generate certification-ready reports in PDF, HTML, or JSON formats for stakeholders and compliance.
            </p>
          </div>
        </div>

        {/* Stats Section */}
        <div className="mt-16 bg-primary-600 rounded-lg shadow-lg p-8 text-white">
          <div className="grid md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-4xl font-bold mb-2">WCAG 2.2</div>
              <div className="text-primary-100">Latest Standard</div>
            </div>
            <div>
              <div className="text-4xl font-bold mb-2">A/AA/AAA</div>
              <div className="text-primary-100">All Levels</div>
            </div>
            <div>
              <div className="text-4xl font-bold mb-2">Multi-Agent</div>
              <div className="text-primary-100">AI Architecture</div>
            </div>
            <div>
              <div className="text-4xl font-bold mb-2">Open Source</div>
              <div className="text-primary-100">LLM Models</div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 dark:border-gray-700 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-gray-600 dark:text-gray-400">
            <p>&copy; 2024 Accessibility Multi-Agent Platform. Building a more inclusive web.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
