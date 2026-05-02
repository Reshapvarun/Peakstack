import React, { useState, useEffect, useCallback } from 'react';
import './App.css';
import { analyzeEnergy, formatCurrency } from './services/api';
import Charts from './components/Charts';
import Insights from './components/Insights';
import Sidebar from './components/Sidebar';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import { motion, AnimatePresence } from 'framer-motion';

export default function App() {
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
  });

  const [response, setResponse]   = useState(null);
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState(null);
  const [darkMode, setDarkMode]   = useState(true);
  const [step, setStep]           = useState(1);

  /* ── Apply dark class to <html> so CSS vars propagate everywhere ── */
  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode);
  }, [darkMode]);

  /* ── Analysis handler ── */
  const handleAnalyze = useCallback(async (currentInputs) => {
    setLoading(true);
    setError(null);
    try {
      const result = await analyzeEnergy(currentInputs);
      setResponse(result);
      setStep(3);
    } catch (err) {
      setError(err.message || 'Analysis failed.');
    } finally {
      setLoading(false);
    }
  }, []);

  /* ── Debounced auto-analysis on input change ── */
  useEffect(() => {
    const t = setTimeout(() => handleAnalyze(inputs), 500);
    return () => clearTimeout(t);
  }, [inputs, handleAnalyze]);

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

  /* ── Render ── */
  return (
    <div className="app-container">
      {/* ── Sidebar ── */}
      <Sidebar
        inputs={inputs}
        updateInput={updateInput}
        loading={loading}
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
              <button className="btn-ghost" onClick={handleDownloadPDF} disabled={!response}>
                📥 Download Report
              </button>
              <button className="btn-ghost" onClick={() => setDarkMode(d => !d)}>
                {darkMode ? '☀️ Light' : '🌙 Dark'}
              </button>
            </div>
          </header>

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
                <p>AI model calculating optimal dispatch…</p>
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

                {/* KPI row */}
                <div className="kpi-grid">
                  <div className="kpi-card">
                    <h4>Monthly Savings</h4>
                    <div className="val">{formatCurrency(response.kpis.monthly_savings_inr)}</div>
                    <div className="change" style={{ color: '#10b981' }}>↑ Demand + Arbitrage</div>
                  </div>
                  <div className="kpi-card">
                    <h4>Payback Period</h4>
                    <div className="val" style={{ color: response.kpis.payback_years === 0 ? '#ef4444' : 'var(--text-main)' }}>
                      {response.kpis.payback_years > 0
                        ? `${response.kpis.payback_years.toFixed(1)} Yrs`
                        : 'Not viable'}
                    </div>
                    <div className="change">incl. 20% lifecycle uplift</div>
                  </div>
                  <div className="kpi-card">
                    <h4>Peak Reduction</h4>
                    <div className="val">{response.kpis.peak_demand_reduction_kw.toFixed(1)} kW</div>
                    <div className="change" style={{ color: '#10b981' }}>↓ Demand charges</div>
                  </div>
                  <div className="kpi-card">
                    <h4>Annual ROI</h4>
                    <div className="val" style={{ color: '#10b981' }}>
                      {response.kpis.roi_percent.toFixed(1)}%
                    </div>
                    <div className="change">on lifecycle cost</div>
                  </div>
                </div>

                {/* Dispatch Panel (Real-time Status) */}
                {(() => {
                  const chart = response.daily_chart;
                  const maxCharge = chart ? Math.max(...(chart.battery_charge_kw || [0])) : 0;
                  const maxDischarge = chart ? Math.max(...(chart.battery_discharge_kw.map(Math.abs) || [0])) : 0;
                  const dgSavings = response.dg_savings?.cost_saved_inr || 0;
                  
                  return (
                    <div className="dispatch-panel">
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
                        <div className="dispatch-icon soc" style={{ background: 'rgba(245, 158, 11, 0.12)' }}>🏭</div>
                        <div className="dispatch-info">
                          <div className="dispatch-label">DG Replacement</div>
                          <div className="dispatch-value">{formatCurrency(dgSavings)}</div>
                          <div className="dispatch-sub">Daily Hybrid Savings</div>
                        </div>
                      </div>
                    </div>
                  );
                })()}

                {/* Sizing Optimizer */}
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

                {/* Charts */}
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

                {/* Insights */}
                <Insights realism={response.realism} insights={response.insights} />
              </motion.div>
            )}

            {/* Empty state (initial) */}
            {!response && !loading && !error && (
              <motion.div
                key="empty"
                className="empty-state"
                initial={{ opacity: 0 }} animate={{ opacity: 1 }}
              >
                <div style={{ fontSize: 52 }}>⚡</div>
                <h3>Configure parameters and run analysis</h3>
                <p>Our AI will simulate 8 760 hours of operation to find your optimal ROI.</p>
              </motion.div>
            )}

          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
