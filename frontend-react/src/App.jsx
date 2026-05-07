import React, { useState, useEffect } from 'react';
import axios from 'axios';
import StatsBar from './components/StatsBar';
import AnomalyCard from './components/AnomalyCard';
import RecommendationModal from './components/RecommendationModal';
import PipelineButton from './components/PipelineButton';

const API_BASE = 'http://localhost:8000';

function App() {
  const [stats, setStats] = useState(null);
  const [anomalies, setAnomalies] = useState([]);
  const [selectedRecommendation, setSelectedRecommendation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch all data
  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch stats
      const statsResponse = await axios.get(`${API_BASE}/stats`);
      setStats(statsResponse.data);

      // Fetch anomalies
      const anomaliesResponse = await axios.get(`${API_BASE}/anomalies`);
      setAnomalies(anomaliesResponse.data.anomalies || []);

      setLoading(false);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('Failed to load data. Make sure the API is running at http://localhost:8000');
      setLoading(false);
    }
  };

  // Fetch recommendation for a specific user
  const fetchRecommendation = async (userId) => {
    try {
      const response = await axios.get(`${API_BASE}/recommendations/${userId}`);
      setSelectedRecommendation(response.data);
    } catch (err) {
      console.error('Error fetching recommendation:', err);
      alert('Failed to load recommendation for ' + userId);
    }
  };

  // Initial data load
  useEffect(() => {
    fetchData();
  }, []);

  // Handle anomaly card click
  const handleAnomalyClick = (anomaly) => {
    fetchRecommendation(anomaly.user_id);
  };

  // Handle modal close
  const handleCloseModal = () => {
    setSelectedRecommendation(null);
  };

  // Handle pipeline success
  const handlePipelineSuccess = () => {
    fetchData();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-beige-100 via-beige-200 to-beige-300 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Navbar */}
        <nav className="bg-white shadow-xl rounded-2xl p-6 mb-8 animate-fadeIn border border-beige-300">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="bg-accent-600 p-3 rounded-xl">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>
              </div>
              <div>
                <h1 className="text-3xl font-bold text-accent-800">Healthmov Insight Engine</h1>
                <p className="text-accent-600 text-sm">AI-Powered Health Anomaly Detection & Personalized Recommendations</p>
              </div>
            </div>
            <PipelineButton onSuccess={handlePipelineSuccess} />
          </div>
        </nav>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border-l-4 border-red-600 text-red-800 p-4 rounded-lg mb-6 animate-fadeIn flex items-center space-x-3 shadow-md">
            <svg className="w-6 h-6 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <p className="font-semibold">Error Loading Data</p>
              <p className="text-sm">{error}</p>
            </div>
          </div>
        )}

        {/* Stats Bar */}
        <StatsBar stats={stats} loading={loading} />

        {/* Anomalies Section */}
        <div className="bg-white shadow-xl rounded-2xl p-8 animate-fadeIn border border-beige-300">
          <div className="flex items-center space-x-3 mb-6 pb-4 border-b border-beige-300">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <h2 className="text-2xl font-bold text-accent-800">Detected Anomalies</h2>
            {!loading && (
              <span className="bg-red-500 text-white px-3 py-1 rounded-full text-sm font-semibold">
                {anomalies.length} flagged
              </span>
            )}
          </div>

          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="bg-beige-100 rounded-xl p-6 animate-pulse border border-beige-300">
                  <div className="h-6 bg-beige-300 rounded mb-4"></div>
                  <div className="h-4 bg-beige-300 rounded mb-2"></div>
                  <div className="h-4 bg-beige-300 rounded mb-2"></div>
                  <div className="h-8 bg-beige-300 rounded"></div>
                </div>
              ))}
            </div>
          ) : anomalies.length === 0 ? (
            <div className="text-center py-12">
              <svg className="w-16 h-16 text-green-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-accent-800 text-xl font-semibold">No anomalies detected</p>
              <p className="text-accent-600 mt-2">All users have normal engagement patterns</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {anomalies.map((anomaly, index) => (
                <div key={index} style={{ animationDelay: `${index * 0.1}s` }}>
                  <AnomalyCard
                    anomaly={anomaly}
                    onClick={() => handleAnomalyClick(anomaly)}
                  />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="text-center mt-8 text-accent-600 text-sm">
          <p>Powered by AI • Multi-Agent System • Real-time Analytics</p>
        </div>
      </div>

      {/* Recommendation Modal */}
      {selectedRecommendation && (
        <RecommendationModal
          recommendation={selectedRecommendation}
          onClose={handleCloseModal}
        />
      )}
    </div>
  );
}

export default App;
