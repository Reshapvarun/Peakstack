import React, { useState, useEffect, useCallback } from 'react';
import './App.css';
import { analyzeEnergy, pollJob, formatCurrency } from './services/api';
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
  });

  const [response, setResponse]   = useState(null);
  const [loading, setLoading]     = useState(false);
  const [uploading, setUploading] = useState(false);
  const [jobStatus, setJobStatus] = useState(null);
  const [error, setError]         = useState(null);
  const [darkMode, setDarkMode]   = useState(true);
  const [step, setStep]           = useState(1);
  const [productMode, setProductMode] = useState('investment'); // 'investment' | 'operations'

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
    // Operations mode requires a CSV — don't auto-analyze without one
    if (productMode === 'operations' && !inputs.csv_file_id) {
      return;
    }
    const t = setTimeout(() => handleAnalyze(inputs), 500);
    return () => clearTimeout(t);
  }, [inputs, handleAnalyze, productMode]);

  const updateInput = (key, value) =>
    setInputs(prev => ({ ...prev, [key]: value }));

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
            {response && !error && (
              <motion.div
                key="results"
                id="report"
                initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.35 }}
              >
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
                {/* Summary bar */}
                <div className="summary-alert">
                  <span style={{ fontSize: 18 }}>✅</span>
                  This facility can save&nbsp;
                  <strong>{formatCurrency(response.kpis.monthly_savings_inr)}/month</strong>
                  &nbsp;with a&nbsp;
                  <strong>{inputs.battery_kwh} kWh BESS</strong> system.
                </div>

                {/* AI Self-Healing Logs (Req #7) */}
                {response.healing_logs && response.healing_logs.length > 0 && (
                  <div className="summary-alert" style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.2)', color: '#d97706' }}>
                    <span style={{ fontSize: 18 }}>🤖</span>
                    <div style={{ flex: 1 }}>
                      <strong>AI Agent Applied {response.healing_logs.length} Auto-Fixes:</strong>
                      <ul style={{ fontSize: 11, marginTop: 4, marginLeft: 16 }}>
                        {response.healing_logs.map((log, i) => (
                          <li key={i}>{log.issue} → {log.fix}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}

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
                      <span className="lbl">Payback</span>
                      <span className="val" style={{ color: response.kpis.payback_years === 0 ? '#ef4444' : 'inherit' }}>
                        {response.kpis.payback_years > 0
                          ? `${response.kpis.payback_years.toFixed(1)} Yrs`
                          : 'Not viable'}
                      </span>
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

                {/* --- MODE SPECIFIC KPI VIEW --- */}
                {productMode === 'investment' ? (
                   <>
                      <div className="kpi-grid">
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
                   </>
                ) : (
                   <>
                      {/* Operations KPIs — null-safe */}
                      {(() => {
                        const chart = response.daily_chart || {};
                        const tariff = chart.tariff || [];
                        const avgIEX = tariff.length > 0
                          ? (tariff.reduce((a, b) => a + b, 0) / tariff.length).toFixed(2)
                          : 'N/A';
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
                   </>
                )}

                {/* Mode-Specific Middle/Bottom Views */}
                {productMode === 'operations' ? (
                   <>
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
                ) : (
                   <>
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

                      {/* Sensitivity Analysis */}
                      <div className="chart-container" style={{ height: 'auto' }}>
                        <div className="chart-header">
                          <h3>Sensitivity Analysis</h3>
                          <span>Risk & Opportunity Impact</span>
                        </div>
                        <div className="sensitivity-list">
                          {(response.sensitivity || []).map(s => (
                            <div key={s.scenario} className="sensitivity-item">
                              <span>{s.scenario}</span>
                              <span className={`impact ${s.savings > response.kpis.annual_savings_inr ? 'positive' : 'negative'}`}>
                                {s.savings > response.kpis.annual_savings_inr ? '↑' : '↓'} 
                                {formatCurrency(Math.abs(s.savings - response.kpis.annual_savings_inr))}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                   </>
                )}

              </motion.div>
            )}

            {/* Empty state — mode-aware */}
            {!response && !loading && !error && (
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
                      background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)',
                      borderRadius: 8, fontSize: 13, color: '#d97706'
                    }}>
                      ⚠️ Real facility data required for this mode
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
