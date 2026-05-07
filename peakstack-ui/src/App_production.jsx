import React, { useState, useEffect, useCallback } from 'react';
import './App.css';
import { analyzeEnergy, pollJob, formatCurrency, getPortfolio, sendControlSignal } from './services/api';
import Charts from './components/Charts';
import Insights from './components/Insights';
import Sidebar from './components/Sidebar';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from './context/AuthContext';
import LoginPage from './pages/LoginPage';

export default function App() {
  const { user, loading: authLoading, logout } = useAuth();
  /* ── Single source of truth ── */
  const [inputs, setInputs] = useState({
    state: 'maharashtra',
    industry: 'manufacturing',
    battery_kwh: 600,
    battery_power_kw: 200,
    solar_kw: 400,
    annual_kwh: 1200000,
    analysis_name: 'Industrial Site A',
    tariff_energy: 8.0,
    demand_charge: 300.0,
    peak_tariff_difference: 3.0,
    battery_cost_per_kwh: 18000.0,
    solar_cost_per_kwh: 3.0,
    utilization_factor: 0.8,
    use_real_data: false,
    horizon_days: 1,
    dg_cost_per_kwh: 20.0,
    dg_hours_per_day: 2.0,
    chemistry: 'lfp',
  });

  const [response, setResponse]   = useState(null);
  const [loading, setLoading]     = useState(false);
  const [uploading, setUploading] = useState(false);
  const [jobStatus, setJobStatus] = useState(null);
  const [error, setError]         = useState(null);
  const [darkMode, setDarkMode]   = useState(true);
  const [step, setStep]           = useState(1);
  const [productMode, setProductMode] = useState('investment'); // 'investment' | 'operations' | 'portfolio'
  const [portfolioData, setPortfolioData] = useState(null);
  const [controlLogs, setControlLogs] = useState([]);

  /* ── Apply dark class to <html> so CSS vars propagate everywhere ── */
  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode);
  }, [darkMode]);

  /* ── Analysis handler ── */
  const handleAnalyze = useCallback(async (currentInputs) => {
    setLoading(true);
    setError(null);
    setJobStatus('initializing');
    try {
      const { job_id } = await analyzeEnergy(currentInputs);
      const result = await pollJob(job_id, (status) => setJobStatus(status));
      setResponse(result);
      setStep(3);
    } catch (err) {
      setError(err.message || 'Analysis failed.');
    } finally {
      setLoading(false);
      setJobStatus(null);
    }
  }, []);

  /* ── Debounced auto-analysis on input change ── */
  useEffect(() => {
    // v3: Auto fallback to synthetic if in operations mode but no CSV
    if (productMode === 'investment') {
      const t = setTimeout(() => handleAnalyze(inputs), 500);
      return () => clearTimeout(t);
    }
  }, [inputs, handleAnalyze, productMode]);

  const updateInput = (key, value) =>
    setInputs(prev => ({ ...prev, [key]: value }));

  const fetchPortfolio = async () => {
    try {
      const data = await getPortfolio();
      setPortfolioData(data);
    } catch (err) {
      console.error("[Portfolio] Error:", err);
    }
  };

  const handleControl = async (device, action, value) => {
    try {
      const signal = { facility_id: 'F-101', device_type: device, action, value };
      await sendControlSignal(device, signal);
      setControlLogs(prev => [`${new Date().toLocaleTimeString()}: ${device.toUpperCase()} ${action.toUpperCase()} executed.`, ...prev.slice(0, 4)]);
    } catch (err) {
      console.error("[Control] Error:", err);
    }
  };

  /* ── PDF export ── */
  const handleDownloadPDF = async () => {
    if (!response) return;
    const el  = document.getElementById('report');
    const cvs = await html2canvas(el, { scale: 2 });
    const img = cvs.toDataURL('image/png');
    const pdf = new jsPDF('l', 'mm', [297, 167]);
    pdf.addImage(img, 'PNG', 0, 0, 297, 167);
    pdf.save('PeakStack_Report.pdf');
  };

  /* ── Recommendation colour ── */
  const recColor =
    response?.recommendation === 'INSTALL BESS'            ? '#10b981' :
    response?.recommendation === 'MARGINAL CASE'           ? '#f59e0b' : '#ef4444';

  if (authLoading) return <div className="loading-state"><div className="spinner"></div></div>;
  if (!user) return <LoginPage />;

  /* ── Render ── */
  return (
    <div className="app-container">
      {/* ── Sidebar ── */}
      <Sidebar 
        inputs={inputs} 
        updateInput={updateInput} 
        loading={loading}
        uploading={uploading}
        setUploading={setUploading}
        productMode={productMode}
        onAnalyze={() => handleAnalyze(inputs)} 
      />

      {/* ── Main panel ── */}
      <main className="main-content">
        <div className="content-inner">

          {/* Header */}
          <header className="header">
            <div className="stepper">
              {[['Configure', 1], ['Analyze', 2], ['Decision', 3]].map(([label, n], i, arr) => (
                <React.Fragment key={label}>
                  <div className={`step ${step >= n ? 'active' : ''}`}>
                    <div className="step-num">{n}</div>
                    {label}
                  </div>
                  {i < arr.length - 1 && (
                    <span style={{ color: 'var(--border)', fontSize: 14 }}>→</span>
                  )}
                </React.Fragment>
              ))}
            </div>

            <div className="header-actions">
              <span style={{ fontSize: 13, marginRight: 10, opacity: 0.6 }}>👤 {user.email}</span>
              <button className="btn-ghost" onClick={logout}>Logout</button>
              <button className="btn-ghost" onClick={handleDownloadPDF} disabled={!response}>
                📥 Download Report
              </button>
              <button className="btn-ghost" onClick={() => setDarkMode(d => !d)}>
                {darkMode ? '☀️ Light' : '🌙 Dark'}
              </button>
            </div>
          </header>

          {/* v3: System Status Bar (Top) */}
          {response && (
            <div className="system-status-bar" style={{ 
              display: 'flex', gap: 20, padding: '8px 20px', background: 'var(--card-bg)', 
              borderRadius: 8, marginBottom: 20, border: '1px solid var(--border)', fontSize: 11,
              textTransform: 'uppercase', letterSpacing: 0.5, fontWeight: 600
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ color: '#10b981' }}>●</span> Solver: {response.system_status?.solver_status || 'Optimal'} ({response.system_status?.solve_time_sec}s)
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ color: '#3b82f6' }}>●</span> Forecast Confidence: {response.system_status?.forecast_confidence}%
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ color: 'var(--accent)' }}>●</span> Mode: {response.system_status?.mode}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginLeft: 'auto' }}>
                Source: {response.system_status?.data_source}
              </div>
            </div>
          )}

          {/* Product Mode Tabs */}
          <div className="product-tabs" style={{ 
            display: 'flex', gap: 12, marginBottom: 24, paddingBottom: 12, borderBottom: '1px solid var(--border)' 
          }}>
            <button 
              className={`tab-btn ${productMode === 'investment' ? 'active' : ''}`}
              onClick={() => {
                setProductMode('investment');
                updateInput('use_real_data', false);
              }}
              style={{
                padding: '8px 16px', borderRadius: '8px', border: '1px solid var(--border)',
                background: productMode === 'investment' ? 'var(--accent)' : 'transparent',
                color: productMode === 'investment' ? '#fff' : 'inherit',
                fontWeight: 'bold', cursor: 'pointer', transition: 'all 0.2s'
              }}
            >
              📊 Investment Analysis
            </button>
            <button 
              className={`tab-btn ${productMode === 'operations' ? 'active' : ''}`}
              onClick={() => {
                setProductMode('operations');
                updateInput('use_real_data', true);
              }}
              style={{
                padding: '8px 16px', borderRadius: '8px', border: '1px solid var(--border)',
                background: productMode === 'operations' ? 'var(--accent)' : 'transparent',
                color: productMode === 'operations' ? '#fff' : 'inherit',
                fontWeight: 'bold', cursor: 'pointer', transition: 'all 0.2s'
              }}
            >
              🔋 Operations / AI Mode
            </button>
            <button 
              className={`tab-btn ${productMode === 'portfolio' ? 'active' : ''}`}
              onClick={() => {
                setProductMode('portfolio');
                fetchPortfolio();
              }}
              style={{
                padding: '8px 16px', borderRadius: '8px', border: '1px solid var(--border)',
                background: productMode === 'portfolio' ? 'var(--accent)' : 'transparent',
                color: productMode === 'portfolio' ? '#fff' : 'inherit',
                fontWeight: 'bold', cursor: 'pointer', transition: 'all 0.2s'
              }}
            >
              🏢 Portfolio Mode
            </button>
          </div>

          {/* Content area */}
          <AnimatePresence mode="wait">

            {/* Loading */}
            {loading && !response && (
              <motion.div
                key="loading"
                className="loading-state"
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              >
                <div className="spinner" />
                <p style={{ maxWidth: '300px', textAlign: 'center' }}>
                  {jobStatus === 'initializing' ? 'Initializing Enterprise Energy Engine...' : 
                   jobStatus === 'ingesting' ? 'Ingesting facility load data...' :
                   jobStatus === 'forecasting' ? 'AI models forecasting solar & load...' :
                   jobStatus === 'optimizing' ? 'MILP Solver calculating optimal dispatch...' :
                   jobStatus === 'calculating' ? 'Finalizing financial performance metrics...' :
                   'AI model calculating optimal dispatch...'}
                </p>
              </motion.div>
            )}

            {/* Error */}
            {error && !loading && (
              <motion.div
                key="error"
                className="empty-state"
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              >
                <div style={{ fontSize: 40 }}>⚠️</div>
                <h3>Analysis Error</h3>
                <p style={{ color: '#ef4444' }}>{error}</p>
              </motion.div>
            )}

            {/* Results */}
            {response && !error && productMode !== 'portfolio' && (
              <motion.div
                key="results"
                id="report"
                initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.35 }}
              >
                {/* v3 Fallback Banner */}
                {productMode === 'operations' && !inputs.csv_file_id && (
                  <div style={{ 
                    background: 'rgba(59, 130, 246, 0.1)', 
                    border: '1px solid rgba(59, 130, 246, 0.3)', 
                    borderRadius: '12px', 
                    padding: '12px 20px', 
                    marginBottom: '20px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px'
                  }}>
                    <span style={{ fontSize: '20px' }}>ℹ️</span>
                    <div>
                      <div style={{ fontWeight: '700', color: '#2563eb', fontSize: '14px' }}>Using Estimated Profile</div>
                      <div style={{ fontSize: '13px', color: '#1d4ed8' }}>
                        No CSV uploaded. System is running operations mode with a synthetic industrial baseline.
                      </div>
                    </div>
                  </div>
                )}

                {/* Data Quality Notice (Req #9) */}
                {response.data_quality_issues && response.data_quality_issues.length > 0 && (
                  <div style={{ 
                    background: 'rgba(245, 158, 11, 0.1)', 
                    border: '1px solid rgba(245, 158, 11, 0.3)', 
                    borderRadius: '12px', 
                    padding: '12px 20px', 
                    marginBottom: '20px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px'
                  }}>
                    <span style={{ fontSize: '20px' }}>📊</span>
                    <div>
                      <div style={{ fontWeight: '700', color: '#d97706', fontSize: '14px' }}>Data Notice</div>
                      <div style={{ fontSize: '13px', color: '#b45309' }}>
                        {response.data_quality_issues.join('. ')}
                      </div>
                    </div>
                  </div>
                )}
                
                {/* Pricing Recommendation (v3) */}
                {response.pricing_recommendation && (
                  <div style={{ 
                    background: 'var(--card-bg)', 
                    border: '2px solid var(--accent)', 
                    borderRadius: '16px', 
                    padding: '20px', 
                    marginBottom: '24px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    boxShadow: '0 8px 32px rgba(0,0,0,0.2)',
                    overflow: 'hidden',
                    position: 'relative'
                  }}>
                    <div style={{ position: 'absolute', right: -20, top: -20, fontSize: 80, opacity: 0.05, pointerEvents: 'none' }}>💰</div>
                    <div>
                      <h3 style={{ fontSize: 18, marginBottom: 4 }}>Value-Based Pricing Recommendation</h3>
                      <p style={{ opacity: 0.7, fontSize: 13 }}>Optimized subscription model based on 8% of projected savings.</p>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: 12, opacity: 0.6, textTransform: 'uppercase' }}>Net Monthly Savings</div>
                      <div style={{ fontSize: 28, fontWeight: 900, color: 'var(--accent)' }}>
                        {formatCurrency(response.pricing_recommendation.net_monthly_savings_after_fee_inr)}
                      </div>
                      <div style={{ fontSize: 11, color: '#10b981', fontWeight: 700 }}>
                        (After ₹{response.pricing_recommendation.monthly_subscription_inr.toLocaleString()} SaaS Fee)
                      </div>
                    </div>
                  </div>
                )}

                {/* Summary bar */}
                <div className="summary-alert">
                  <span style={{ fontSize: 18 }}>✅</span>
                  This facility can save&nbsp;
                  <strong>{formatCurrency(response.kpis.monthly_savings_inr)}/month</strong>
                  &nbsp;with a&nbsp;
                  <strong>{inputs.battery_kwh} kWh {inputs.chemistry?.toUpperCase()}</strong> system.
                </div>

                {/* Recommendation hero */}
                <div className="rec-hero">
                  <div className="rec-icon">🏆</div>
                  <div className="rec-details">
                    <h4>Investment Recommendation</h4>
                    <h2 style={{ color: recColor }}>{response.recommendation}</h2>
                    <p>{response.recommendation_reason}</p>
                  </div>
                  <div className="rec-metrics">
                    <div className="rec-metric-item">
                      <span className="lbl">Capacity</span>
                      <span className="val">{inputs.battery_kwh} kWh</span>
                    </div>
                    <div className="rec-metric-item">
                      <span className="lbl">Chemistry</span>
                      <span className="val" style={{ textTransform: 'uppercase' }}>{inputs.chemistry || 'LFP'}</span>
                    </div>
                    <div className="rec-metric-item">
                      <span className="lbl">Confidence</span>
                      <span
                        className="val"
                        style={{
                          fontSize: 14,
                          background: response.realism.confidence_score > 0.8 ? '#10b981' : '#f59e0b',
                          color: '#fff',
                          padding: '3px 10px',
                          borderRadius: 4,
                        }}
                      >
                        {(response.realism.confidence_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* ESG Dashboard (v3) */}
                {response.esg && (
                  <div style={{ marginBottom: 24 }}>
                    <h3 style={{ fontSize: 14, marginBottom: 16, opacity: 0.8, textTransform: 'uppercase', letterSpacing: 1 }}>ESG & Sustainability Impact</h3>
                    <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
                      <div className="kpi-card" style={{ borderLeft: '4px solid #10b981' }}>
                        <h4>CO₂ Offset</h4>
                        <div className="val" style={{ color: '#10b981' }}>{response.esg.co2_offset_kg.toLocaleString()} kg</div>
                        <div className="change">Annual Carbon Avoided</div>
                      </div>
                      <div className="kpi-card" style={{ borderLeft: '4px solid #3b82f6' }}>
                        <h4>Diesel Saved</h4>
                        <div className="val" style={{ color: '#3b82f6' }}>{response.esg.diesel_saved_litres.toLocaleString()} L</div>
                        <div className="change">Fossil Fuel Offset</div>
                      </div>
                      <div className="kpi-card" style={{ borderLeft: '4px solid #f59e0b' }}>
                        <h4>Renewable Fraction</h4>
                        <div className="val" style={{ color: '#f59e0b' }}>{response.esg.renewable_fraction_percent}%</div>
                        <div className="change">Total Energy Mix</div>
                      </div>
                      <div className="kpi-card" style={{ borderLeft: '4px solid #059669' }}>
                        <h4>Tree Equivalent</h4>
                        <div className="val" style={{ color: '#059669' }}>{response.esg.trees_equivalent}</div>
                        <div className="change">Mature Trees / Year</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* --- MODE SPECIFIC KPI VIEW --- */}
                {productMode === 'investment' ? (
                   <>
                      <div className="kpi-grid" style={{ marginBottom: 20 }}>
                        <div className="kpi-card">
                          <h4>Annual Savings</h4>
                          <div className="val">{formatCurrency(response.kpis.annual_savings_inr)}</div>
                          <div className="change" style={{ color: '#10b981' }}>↑ Optimised BESS</div>
                        </div>
                        <div className="kpi-card">
                          <h4>Payback Period</h4>
                          <div className="val">{response.kpis.payback_years.toFixed(1)} Yrs</div>
                          <div className="change">incl. 20% lifecycle uplift</div>
                        </div>
                        <div className="kpi-card">
                          <h4>Annual ROI</h4>
                          <div className="val" style={{ color: '#10b981' }}>{response.kpis.roi_percent.toFixed(1)}%</div>
                          <div className="change">Internal Rate of Return</div>
                        </div>
                        <div className="kpi-card">
                          <h4>NPV (10Y)</h4>
                          <div className="val">{formatCurrency(response.kpis.npv_10yr_inr)}</div>
                          <div className="change">Net Present Value</div>
                        </div>
                      </div>

                      {/* Savings Breakdown (Advanced) */}
                      <div style={{ marginBottom: 24 }}>
                        <h3 style={{ fontSize: 14, marginBottom: 16, opacity: 0.8, textTransform: 'uppercase', letterSpacing: 1 }}>Savings Decomposition</h3>
                        <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
                          <div className="kpi-card" style={{ background: 'rgba(255,255,255,0.02)' }}>
                            <h4 style={{ fontSize: 10 }}>Peak Shaving</h4>
                            <div className="val" style={{ fontSize: 16 }}>{formatCurrency(response.savings_breakdown?.peak_shaving_inr)}</div>
                          </div>
                          <div className="kpi-card" style={{ background: 'rgba(255,255,255,0.02)' }}>
                            <h4 style={{ fontSize: 10 }}>IEX Arbitrage</h4>
                            <div className="val" style={{ fontSize: 16 }}>{formatCurrency(response.savings_breakdown?.arbitrage_inr)}</div>
                          </div>
                          <div className="kpi-card" style={{ background: 'rgba(255,255,255,0.02)' }}>
                            <h4 style={{ fontSize: 10 }}>DG Replacement</h4>
                            <div className="val" style={{ fontSize: 16 }}>{formatCurrency(response.savings_breakdown?.dg_savings_inr)}</div>
                          </div>
                          <div className="kpi-card" style={{ background: 'rgba(255,255,255,0.02)' }}>
                            <h4 style={{ fontSize: 10 }}>Solar Opt.</h4>
                            <div className="val" style={{ fontSize: 16 }}>{formatCurrency(response.savings_breakdown?.solar_utilization_inr)}</div>
                          </div>
                        </div>
                      </div>
                      
                      {/* Sizing Optimizer (Investment Only) */}
                      <div style={{ marginBottom: 24 }}>
                        <h3 style={{ fontSize: 14, marginBottom: 12, opacity: 0.8 }}>Recommended System Size</h3>
                        <div className="sizing-grid">
                          {[100, 200, 300, 400, 600, 800, 1000].map(size => {
                            const isBest = response.recommended_sizing?.size === size;
                            return (
                              <div key={size} className={`sizing-card ${isBest ? 'recommended' : ''}`}>
                                <div style={{ fontSize: 10, textTransform: 'uppercase', color: 'var(--text-muted)' }}>Capacity</div>
                                <div style={{ fontSize: 18, fontWeight: 800, margin: '4px 0' }}>{size} kWh</div>
                                <div style={{ fontSize: 11, color: isBest ? 'var(--accent)' : 'var(--text-muted)' }}>
                                  {isBest ? '⭐ Optimal ROI' : `ROI: ${(response.kpis.roi_percent * (1 - Math.abs(size-inputs.battery_kwh)/2000)).toFixed(1)}%`}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                      <div className="charts-grid">
                      {/* Scenario Comparison */}
                      <div className="chart-container" style={{ height: 'auto' }}>
                        <div className="chart-header">
                          <h3>Scenario Comparison</h3>
                          <span>Baseline vs Current vs AI-Optimized</span>
                        </div>
                        <table className="scenario-table">
                          <thead>
                            <tr>
                              <th>Scenario</th>
                              <th>Annual Savings</th>
                              <th>Payback</th>
                              <th>ROI</th>
                            </tr>
                          </thead>
                          <tbody>
                            {(response.scenarios || []).map(s => (
                              <tr key={s.name}>
                                <td style={{ fontWeight: 600 }}>{s.name}</td>
                                <td>{formatCurrency(s.savings)}</td>
                                <td>{s.payback ? `${s.payback.toFixed(1)} yrs` : '-'}</td>
                                <td style={{ color: 'var(--accent)', fontWeight: 700 }}>{s.roi.toFixed(1)}%</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>

                      {/* Financial Risk Bands (v3) */}
                      <div className="chart-container" style={{ height: 'auto' }}>
                        <div className="chart-header">
                          <h3>Investor Risk Bands</h3>
                          <span>Projected Savings Scenarios</span>
                        </div>
                        <div className="sensitivity-list">
                          <div className="sensitivity-item">
                            <span>🛡️ Conservative (-15%)</span>
                            <span className="impact negative" style={{ color: '#ef4444' }}>
                              {formatCurrency(response.kpis.annual_savings_inr * 0.85)}
                            </span>
                          </div>
                          <div className="sensitivity-item" style={{ background: 'rgba(99,102,241,0.1)', border: '1px solid var(--accent)' }}>
                            <span>🎯 Expected (Baseline)</span>
                            <span className="impact" style={{ color: 'var(--accent)' }}>
                              {formatCurrency(response.kpis.annual_savings_inr)}
                            </span>
                          </div>
                          <div className="sensitivity-item">
                            <span>🚀 Aggressive (+12%)</span>
                            <span className="impact positive" style={{ color: '#10b981' }}>
                              {formatCurrency(response.kpis.annual_savings_inr * 1.12)}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                   </>
                ) : (
                   <>
                      {/* Operations KPIs — null-safe */}
                      {(() => {
                        const chart = response.daily_chart || {};
                        const firstLoad = (chart.load_kw || [])[0];
                        const dgSavings = response.dg_savings?.cost_saved_inr || 0;
                        const dgKwh = response.dg_savings?.energy_replaced_kwh || 0;
                        return (
                          <div className="kpi-grid">
                            <div className="kpi-card">
                              <h4>Facility Load (t=0)</h4>
                              <div className="val">{firstLoad != null ? firstLoad.toFixed(1) : '—'} kW</div>
                              <div className="change" style={{ color: '#10b981' }}>Current Demand</div>
                            </div>
                            <div className="kpi-card">
                              <h4>Peak Reduction</h4>
                              <div className="val">{response.kpis.peak_demand_reduction_kw.toFixed(1)} kW</div>
                              <div className="change" style={{ color: '#10b981' }}>↓ Demand charge avoided</div>
                            </div>
                            <div className="kpi-card">
                              <h4>DG Energy Replaced</h4>
                              <div className="val">{dgKwh.toFixed(1)} kWh</div>
                              <div className="change" style={{ color: '#f59e0b' }}>Hybrid Savings</div>
                            </div>
                            <div className="kpi-card">
                              <h4>DG Cost Offset</h4>
                              <div className="val">{formatCurrency(dgSavings)}</div>
                              <div className="change" style={{ color: '#f59e0b' }}>Daily Diesel Savings</div>
                            </div>
                          </div>
                        );
                      })()}

                      {/* DG Intelligence Panel (v3) */}
                      <div style={{ marginBottom: 24 }}>
                        <h3 style={{ fontSize: 14, marginBottom: 16, opacity: 0.8, textTransform: 'uppercase', letterSpacing: 1 }}>DG Intelligence & Optimization</h3>
                        <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
                          <div className="kpi-card" style={{ borderLeft: '4px solid #ef4444' }}>
                            <h4>DG Runtime</h4>
                            <div className="val" style={{ color: '#ef4444' }}>{response.dg_intelligence?.runtime_hrs} hrs/day</div>
                            <div className="change">Facility Baseline</div>
                          </div>
                          <div className="kpi-card" style={{ borderLeft: '4px solid #f59e0b' }}>
                            <h4>DG Replaced</h4>
                            <div className="val" style={{ color: '#f59e0b' }}>{response.dg_intelligence?.replaced_percent}%</div>
                            <div className="change">BESS Substitution</div>
                          </div>
                          <div className="kpi-card" style={{ borderLeft: '4px solid #10b981' }}>
                            <h4>Diesel Saved</h4>
                            <div className="val" style={{ color: '#10b981' }}>{response.dg_intelligence?.diesel_saved_litres} L</div>
                            <div className="change">Daily Offset</div>
                          </div>
                          <div className="kpi-card" style={{ borderLeft: '4px solid #var(--accent)' }}>
                            <h4>Daily DG Savings</h4>
                            <div className="val" style={{ color: 'var(--accent)' }}>{formatCurrency(response.dg_intelligence?.savings_inr)}</div>
                            <div className="change">Fuel Cost Avoided</div>
                          </div>
                        </div>
                      </div>

                      {/* Battery Health Panel (v3) */}
                      <div style={{ marginBottom: 24 }}>
                        <h3 style={{ fontSize: 14, marginBottom: 16, opacity: 0.8, textTransform: 'uppercase', letterSpacing: 1 }}>BESS Health & Longevity</h3>
                        <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
                          <div className="kpi-card">
                            <h4>Cycles / Day</h4>
                            <div className="val">{response.battery_health?.cycles_per_day}</div>
                            <div className="change">Charge-Discharge Intensity</div>
                          </div>
                          <div className="kpi-card">
                            <h4>Degradation Cost</h4>
                            <div className="val">{formatCurrency(response.battery_health?.degradation_cost_inr)}</div>
                            <div className="change">Daily CapEx Amortization</div>
                          </div>
                          <div className="kpi-card">
                            <h4>Estimated Life</h4>
                            <div className="val" style={{ color: '#10b981' }}>{response.battery_health?.estimated_life_years} Yrs</div>
                            <div className="change">Based on 6000 Cycle LFP</div>
                          </div>
                          <div className="kpi-card">
                            <h4>Health (SOH)</h4>
                            <div className="val" style={{ color: '#10b981' }}>{response.battery_health?.state_of_health_percent}%</div>
                            <div className="change">Current Capacity Integrity</div>
                          </div>
                        </div>
                      </div>

                      {/* Control Center */}
                      <div style={{ marginBottom: 24, marginTop: 24 }}>
                        <h3 style={{ fontSize: 14, marginBottom: 16, opacity: 0.8, textTransform: 'uppercase', letterSpacing: 1 }}>Autonomous Control Center</h3>
                        <div className="dispatch-panel" style={{ background: 'rgba(0,0,0,0.2)', padding: 16, borderRadius: 12 }}>
                          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                            <button className="btn-primary" onClick={() => handleControl('bess', 'discharge', 100)} style={{ fontSize: 12 }}>⚡ BESS Discharge (100kW)</button>
                            <button className="btn-primary" onClick={() => handleControl('bess', 'charge', 50)} style={{ fontSize: 12 }}>🔌 BESS Charge (50kW)</button>
                            <button className="btn-primary" style={{ background: '#ef4444', fontSize: 12 }} onClick={() => handleControl('dg', 'stop', 0)}>🛑 Emergency DG Stop</button>
                          </div>
                          <div style={{ marginTop: 12, fontSize: 11, opacity: 0.7, background: '#000', padding: 8, borderRadius: 4, minHeight: 60 }}>
                            <div style={{ color: 'var(--accent)', fontWeight: 700, marginBottom: 4 }}>Control Signal Stream:</div>
                            {controlLogs.length > 0 ? controlLogs.map((log, i) => <div key={i}>{log}</div>) : 'Waiting for autonomous trigger...'}
                          </div>
                        </div>
                      </div>

                      {(() => {
                        const chart = response.daily_chart || {};
                        const chargeArr = chart.battery_charge_kw || [0];
                        const dischargeArr = chart.battery_discharge_kw || [0];
                        const maxCharge = Math.max(...chargeArr);
                        const maxDischarge = Math.abs(Math.min(...dischargeArr));
                        const dgSavings = response.dg_savings?.cost_saved_inr || 0;
                        return (
                          <div className="dispatch-panel" style={{ marginBottom: 24 }}>
                            <div className="dispatch-card">
                              <div className="dispatch-icon charge">⚡</div>
                              <div className="dispatch-info">
                                <div className="dispatch-label">Peak Charge</div>
                                <div className="dispatch-value">{maxCharge.toFixed(1)} kW</div>
                                <div className="dispatch-sub">Off-peak window</div>
                              </div>
                            </div>
                            <div className="dispatch-card">
                              <div className="dispatch-icon discharge">🔋</div>
                              <div className="dispatch-info">
                                <div className="dispatch-label">Peak Discharge</div>
                                <div className="dispatch-value">{maxDischarge.toFixed(1)} kW</div>
                                <div className="dispatch-sub">Max Arbitrage</div>
                              </div>
                            </div>
                            <div className="dispatch-card">
                              <div className="dispatch-icon soc" style={{ background: 'rgba(245,158,11,0.1)' }}>🏭</div>
                              <div className="dispatch-info">
                                <div className="dispatch-label">DG Offset</div>
                                <div className="dispatch-value">{formatCurrency(dgSavings)}</div>
                                <div className="dispatch-sub">Daily Hybrid Savings</div>
                              </div>
                            </div>
                          </div>
                        );
                      })()}

                      <div className="charts-grid">
                        <div className="chart-container">
                          <div className="chart-header">
                            <h3>Grid Impact Analysis</h3>
                            <span>Import Profile (kW)</span>
                          </div>
                          <Charts dailyChart={response.daily_chart} type="comparison" />
                        </div>
                        <div className="chart-container">
                          <div className="chart-header">
                            <h3>Optimal Dispatch Profile</h3>
                            <span>15-min Charge / Discharge / SOC</span>
                          </div>
                          <Charts dailyChart={response.daily_chart} type="profile" />
                        </div>
                      </div>
                      
                      <Insights insights={response.insights} realism={response.realism} />
                   </>
                )}
              </motion.div>
            )}

            {/* v4: Portfolio Mode View */}
            {productMode === 'portfolio' && portfolioData && (
              <motion.div
                key="portfolio"
                initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                style={{ paddingBottom: 60 }}
              >
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 32 }}>
                  <div className="kpi-card" style={{ borderTop: '4px solid var(--accent)' }}>
                    <h4>Total Facilities</h4>
                    <div className="val">{portfolioData.total_facilities}</div>
                  </div>
                  <div className="kpi-card" style={{ borderTop: '4px solid #10b981' }}>
                    <h4>Portfolio Capacity</h4>
                    <div className="val">{portfolioData.total_battery_capacity_kwh.toLocaleString()} kWh</div>
                  </div>
                  <div className="kpi-card" style={{ borderTop: '4px solid #3b82f6' }}>
                    <h4>Aggregated Savings</h4>
                    <div className="val">{formatCurrency(portfolioData.total_monthly_savings_inr)}/mo</div>
                  </div>
                  <div className="kpi-card" style={{ borderTop: '4px solid #f59e0b' }}>
                    <h4>Portfolio ROI</h4>
                    <div className="val">{portfolioData.portfolio_roi_percent}%</div>
                  </div>
                </div>

                <h3 style={{ fontSize: 16, marginBottom: 16 }}>Facility Fleet Status</h3>
                <div style={{ background: 'var(--card-bg)', borderRadius: 12, border: '1px solid var(--border)', overflow: 'hidden' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                    <thead style={{ background: 'rgba(255,255,255,0.05)', fontSize: 12, textTransform: 'uppercase' }}>
                      <tr>
                        <th style={{ padding: '12px 20px' }}>Site Name</th>
                        <th>State</th>
                        <th>BESS Size</th>
                        <th>Monthly Savings</th>
                        <th>System Health</th>
                      </tr>
                    </thead>
                    <tbody style={{ fontSize: 13 }}>
                      {portfolioData.facilities.map(f => (
                        <tr key={f.facility_id} style={{ borderBottom: '1px solid var(--border)' }}>
                          <td style={{ padding: '16px 20px', fontWeight: 600 }}>{f.name}</td>
                          <td>{f.state}</td>
                          <td>{f.battery_kwh} kWh</td>
                          <td style={{ color: 'var(--accent)', fontWeight: 700 }}>{formatCurrency(f.monthly_savings_inr)}</td>
                          <td>
                            <span style={{ 
                              padding: '2px 8px', borderRadius: 4, fontSize: 11, 
                              background: f.status === 'Online' ? 'rgba(16,185,129,0.1)' : 'rgba(59,130,246,0.1)',
                              color: f.status === 'Online' ? '#10b981' : '#3b82f6'
                            }}>
                              ● {f.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </motion.div>
            )}

            {/* v3: No blank screen ever — if not results and not loading, show empty/fallback info */}
            {!response && !loading && !error && productMode !== 'portfolio' && (
              <motion.div
                key="empty"
                className="empty-state"
                initial={{ opacity: 0 }} animate={{ opacity: 1 }}
              >
                {productMode === 'investment' ? (
                  <>
                    <div style={{ fontSize: 52 }}>📊</div>
                    <h3>Investment Analysis Mode</h3>
                    <p>Configure your BESS system parameters in the sidebar.<br/>Results will appear automatically using synthetic load data.</p>
                  </>
                ) : (
                  <>
                    <div style={{ fontSize: 52 }}>🔋</div>
                    <h3>Operations / AI Mode</h3>
                    <p style={{ maxWidth: 340 }}>Upload your facility's CSV load data using the sidebar to activate ML forecasting, MILP dispatch optimisation, and real-time IEX pricing.</p>
                    <div style={{
                      marginTop: 16, padding: '12px 20px',
                      background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.3)',
                      borderRadius: 8, fontSize: 13, color: '#2563eb'
                    }}>
                      💡 System will fallback to synthetic data if no CSV is provided
                    </div>
                  </>
                )}
              </motion.div>
            )}

          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
