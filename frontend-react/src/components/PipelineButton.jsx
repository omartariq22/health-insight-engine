import React, { useState } from 'react';
import axios from 'axios';

const PipelineButton = ({ onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null); // 'success', 'error', null

  const handleRunPipeline = async () => {
    setLoading(true);
    setStatus(null);

    try {
      // Trigger the pipeline
      const response = await axios.post('http://localhost:8000/run-pipeline');
      
      if (response.data.status === 'started') {
        // Poll for completion
        const checkStatus = setInterval(async () => {
          try {
            const statusResponse = await axios.get('http://localhost:8000/pipeline-status');
            
            if (!statusResponse.data.running) {
              clearInterval(checkStatus);
              
              if (statusResponse.data.error) {
                setStatus('error');
                setLoading(false);
              } else {
                setStatus('success');
                setLoading(false);
                
                // Refresh dashboard data after 2 seconds
                setTimeout(() => {
                  if (onSuccess) onSuccess();
                  setStatus(null);
                }, 2000);
              }
            }
          } catch (error) {
            clearInterval(checkStatus);
            setStatus('error');
            setLoading(false);
          }
        }, 2000); // Check every 2 seconds
      }
    } catch (error) {
      console.error('Error running pipeline:', error);
      setStatus('error');
      setLoading(false);
      
      // Reset error status after 3 seconds
      setTimeout(() => setStatus(null), 3000);
    }
  };

  return (
    <div className="flex items-center space-x-4">
      <button
        onClick={handleRunPipeline}
        disabled={loading}
        className={`
          relative px-8 py-4 rounded-xl font-bold text-lg shadow-lg
          transform transition-all duration-300
          ${loading 
            ? 'bg-gray-400 cursor-not-allowed' 
            : status === 'success'
            ? 'bg-green-600 hover:bg-green-700'
            : status === 'error'
            ? 'bg-red-600 hover:bg-red-700'
            : 'bg-gradient-to-r from-accent-700 to-accent-600 hover:from-accent-800 hover:to-accent-700 hover:shadow-2xl hover:-translate-y-1'
          }
          text-white
          flex items-center space-x-3
        `}
      >
        {loading ? (
          <>
            <svg className="animate-spin h-6 w-6" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>Running Pipeline...</span>
          </>
        ) : status === 'success' ? (
          <>
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Pipeline Complete!</span>
          </>
        ) : status === 'error' ? (
          <>
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Pipeline Failed</span>
          </>
        ) : (
          <>
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Run Pipeline</span>
          </>
        )}
      </button>

      {loading && (
        <div className="text-accent-700 text-sm animate-pulse font-semibold">
          Detecting anomalies and generating recommendations...
        </div>
      )}
    </div>
  );
};

export default PipelineButton;
