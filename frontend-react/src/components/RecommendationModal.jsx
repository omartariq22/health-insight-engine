import React from 'react';

const RecommendationModal = ({ recommendation, onClose }) => {
  if (!recommendation) return null;

  const anomaly = recommendation.anomaly_report;
  const uniqueSources = [...new Set(recommendation.rag_sources)];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fadeIn">
      <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-2xl animate-fadeIn border border-beige-300">
        {/* Header */}
        <div className="sticky top-0 bg-gradient-to-r from-accent-700 to-accent-600 text-white p-6 rounded-t-2xl flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h2 className="text-2xl font-bold">Recommendation for {anomaly.user_name || recommendation.user_id}</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white hover:bg-opacity-20 rounded-full transition-all duration-200 transform hover:rotate-90"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-8">
          {/* Anomaly Details Box */}
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 border-l-4 border-accent-700 rounded-lg p-6 mb-6">
            <div className="flex items-center space-x-2 mb-4">
              <svg className="w-6 h-6 text-accent-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className="text-xl font-bold text-accent-800">Anomaly Details</h3>
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="flex items-center space-x-2">
                <svg className="w-5 h-5 text-accent-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <div>
                  <span className="font-semibold text-gray-700">Metric:</span>
                  <span className="ml-2 text-gray-900">{anomaly.metric.replace('_', ' ')}</span>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div>
                  <span className="font-semibold text-gray-700">Drop:</span>
                  <span className="ml-2 text-red-700 font-bold">{anomaly.drop_percentage}% ({anomaly.severity})</span>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <svg className="w-5 h-5 text-accent-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <div>
                  <span className="font-semibold text-gray-700">Baseline:</span>
                  <span className="ml-2 text-gray-900">{anomaly.baseline_avg}</span>
                  <span className="text-xs text-gray-500 ml-1">({anomaly.baseline_period})</span>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <svg className="w-5 h-5 text-accent-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
                <div>
                  <span className="font-semibold text-gray-700">Recent:</span>
                  <span className="ml-2 text-gray-900">{anomaly.recent_avg}</span>
                  <span className="text-xs text-gray-500 ml-1">({anomaly.recent_period})</span>
                </div>
              </div>
            </div>
          </div>

          {/* Recommendation Text */}
          <div className="mb-6">
            <div className="flex items-center space-x-2 mb-4">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className="text-xl font-bold text-accent-800">Personalized Recommendation</h3>
            </div>
            <div className="bg-beige-100 border border-beige-300 rounded-lg p-6 text-gray-800 leading-relaxed whitespace-pre-wrap">
              {recommendation.recommendation}
            </div>
          </div>

          {/* RAG Sources */}
          <div className="bg-gradient-to-br from-indigo-50 to-indigo-100 border border-indigo-200 rounded-lg p-6 mb-6">
            <div className="flex items-center space-x-2 mb-4">
              <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              <h4 className="text-lg font-bold text-indigo-900">Evidence-Based Sources</h4>
            </div>
            <ul className="space-y-3">
              {uniqueSources.map((source, index) => (
                <li key={index} className="flex items-start space-x-3 text-indigo-900">
                  <svg className="w-5 h-5 mt-0.5 flex-shrink-0 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="text-sm">{source}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Timestamp */}
          <div className="flex items-center space-x-2 text-sm text-gray-500 pt-4 border-t border-beige-300">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Created: {new Date(recommendation.created_at).toLocaleString()}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RecommendationModal;
