import React from 'react';

const AnomalyCard = ({ anomaly, onClick }) => {
  const severityConfig = {
    severe: {
      bg: 'bg-gradient-to-br from-red-50 to-red-100',
      border: 'border-l-4 border-red-600',
      badge: 'bg-red-100 text-red-800 border border-red-200',
      icon: 'text-red-600',
      dropColor: 'text-red-700',
    },
    moderate: {
      bg: 'bg-gradient-to-br from-orange-50 to-orange-100',
      border: 'border-l-4 border-orange-500',
      badge: 'bg-orange-100 text-orange-800 border border-orange-200',
      icon: 'text-orange-600',
      dropColor: 'text-orange-700',
    },
  };

  const config = severityConfig[anomaly.severity] || severityConfig.moderate;

  const metricIcons = {
    steps: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
    sleep_hours: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
      </svg>
    ),
    heart_rate: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
      </svg>
    ),
  };

  return (
    <div
      onClick={onClick}
      className={`${config.bg} ${config.border} rounded-xl p-6 cursor-pointer hover:shadow-2xl transform hover:-translate-y-2 transition-all duration-300 animate-fadeIn border border-beige-300`}
    >
      {/* User Header */}
      <div className="flex items-center justify-between mb-4 pb-4 border-b border-gray-300">
        <div className="flex items-center space-x-2">
          <svg className="w-6 h-6 text-accent-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
          <span className="text-lg font-bold text-accent-800">{anomaly.user_name || anomaly.user_id}</span>
        </div>
        <div className="flex items-center space-x-2 bg-accent-700 text-white px-3 py-1 rounded-full text-sm font-semibold">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <span>Age {anomaly.age}</span>
        </div>
      </div>

      {/* Metric Info */}
      <div className="flex items-center space-x-2 mb-3 text-gray-700">
        <div className={config.icon}>
          {metricIcons[anomaly.metric] || metricIcons.steps}
        </div>
        <span className="font-medium">Metric:</span>
        <span className="font-semibold">{anomaly.metric.replace('_', ' ')}</span>
      </div>

      {/* Drop Percentage */}
      <div className={`text-4xl font-bold ${config.dropColor} mb-4 flex items-center space-x-2`}>
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
        </svg>
        <span>{anomaly.drop_percentage}%</span>
      </div>

      {/* Severity Badge */}
      <div className="mb-4">
        <span className={`${config.badge} px-4 py-2 rounded-full text-sm font-bold uppercase tracking-wide inline-flex items-center space-x-2`}>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <span>{anomaly.severity}</span>
        </span>
      </div>

      {/* Baseline vs Recent */}
      <div className="space-y-2 text-sm text-gray-700 mb-4">
        <div className="flex items-start space-x-2">
          <svg className="w-4 h-4 mt-0.5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <div>
            <span className="font-semibold">Baseline:</span> {anomaly.baseline_avg}
            <div className="text-xs text-gray-500">({anomaly.baseline_period})</div>
          </div>
        </div>
        <div className="flex items-start space-x-2">
          <svg className="w-4 h-4 mt-0.5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
          </svg>
          <div>
            <span className="font-semibold">Recent:</span> {anomaly.recent_avg}
            <div className="text-xs text-gray-500">({anomaly.recent_period})</div>
          </div>
        </div>
      </div>

      {/* View Recommendation CTA */}
      <div className="flex items-center justify-between text-accent-700 font-semibold pt-4 border-t border-gray-300">
        <span>View Recommendation</span>
        <svg className="w-5 h-5 transform group-hover:translate-x-2 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
        </svg>
      </div>
    </div>
  );
};

export default AnomalyCard;
