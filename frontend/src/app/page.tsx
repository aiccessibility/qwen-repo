'use client';

import { useState } from 'react';
import { Activity, Shield, FileText, Play } from 'lucide-react';

export default function Home() {
  const [url, setUrl] = useState('');
  const [isAuditing, setIsAuditing] = useState(false);

  const handleStartAudit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;

    setIsAuditing(true);
    
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/accessibility/audit`, {
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
      alert(`Audit started! ID: ${data.audit_id}`);
    } catch (error) {
      console.error('Error starting audit:', error);
      alert('Error starting audit. Please try again.');
    } finally {
      setIsAuditing(false);
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
              <a href="#" className="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white">
                Dashboard
              </a>
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
