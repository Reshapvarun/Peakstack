import React, { useEffect, useState } from 'react';
import { getSupportedStates } from '../api/client';
import logo from '../assets/logo.png';

export default function Sidebar({ 
  state, setState, 
  annualKwh, setAnnualKwh, 
  batteryKwh, setBatteryKwh, 
  batteryPowerKw, setBatteryPowerKw, 
  onAnalyze, loading, error 
}) {
  const [availableStates, setAvailableStates] = useState(['tamil_nadu', 'maharashtra', 'karnataka']);

  useEffect(() => {
    const fetchStates = async () => {
      try {
        const data = await getSupportedStates();
        if (data.supported_states) {
          setAvailableStates(data.supported_states);
        }
      } catch (err) {
        console.error("Failed to load states", err);
      }
    };
    fetchStates();
  }, []);

  return (
    <aside className="sidebar">
      <div className="logo-section">
        <img src={logo} className="logo-img" alt="Peakstack" />
        <div style={{ fontSize: 10, opacity: 0.5, marginTop: 4 }}>v2.0 (Investor Ready)</div>
      </div>

      <div className="sidebar-group">
        <h3>FACILITY CONFIGURATION</h3>
        
        <div className="form-group">
          <label>Location (State/UT)</label>
          <select 
            value={state} 
            onChange={(e) => setState(e.target.value)}
            disabled={loading}
          >
            {availableStates.map(s => (
              <option key={s} value={s}>
                {s.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Annual Consumption (kWh)</label>
          <input 
            type="number" 
            value={annualKwh} 
            onChange={(e) => setAnnualKwh(parseFloat(e.target.value) || 0)}
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label>Battery Capacity (kWh)</label>
          <input 
            type="number" 
            value={batteryKwh} 
            onChange={(e) => setBatteryKwh(parseFloat(e.target.value) || 0)}
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label>Battery Power Rating (kW)</label>
          <input 
            type="number" 
            value={batteryPowerKw} 
            onChange={(e) => setBatteryPowerKw(parseFloat(e.target.value) || 0)}
            disabled={loading}
          />
        </div>
      </div>

      {error && (
        <div style={{ color: '#ef4444', fontSize: '12px', marginBottom: '16px', padding: '10px', background: 'rgba(239,68,68,0.1)', borderRadius: '4px' }}>
          ⚠️ {error}
        </div>
      )}

      <button 
        className="btn-analyze" 
        onClick={onAnalyze}
        disabled={loading}
      >
        {loading ? '⏳ PROCESSING...' : '🚀 RUN INVESTMENT ANALYSIS'}
      </button>
    </aside>
  );
}