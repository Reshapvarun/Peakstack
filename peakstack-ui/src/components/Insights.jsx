import React from 'react';
import PropTypes from 'prop-types';
import { formatCurrency } from '../services/api';

export default function Insights({ 
  insights, 
  realism
}) {
  if (!realism || !insights) return null;

  return (
    <div className="insights-wrapper" style={{ marginTop: '16px' }}>
      <div className="charts-grid">
        {/* Realism Gap Section */}
        <div className="chart-container" style={{ gridColumn: 'span 1', height: 'auto', minHeight: '220px' }}>
          <div className="chart-header">
            <h3>AI Confidence & Realism</h3>
            <div style={{ 
              background: realism.confidence_score > 0.8 ? '#10b981' : '#f59e0b', 
              color: 'white', padding: '2px 8px', borderRadius: '4px', fontSize: '12px', fontWeight: 'bold' 
            }}>
              {realism.confidence_score > 0.8 ? 'HIGH' : 'MODERATE'}
            </div>
          </div>
          
          <div className="realism-content" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
             <p style={{ fontSize: '14px', color: 'var(--text-muted)', lineHeight: '1.5' }}>
              {realism.confidence_reason}
             </p>
             
             <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '20px', background: 'var(--bg-main)', borderRadius: '12px', border: '1px solid var(--border)' }}>
                <div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Theoretical Savings</div>
                  <div style={{ fontSize: '20px', fontWeight: '800' }}>{formatCurrency(realism.theoretical_savings_inr)}</div>
                </div>
                <div style={{ fontSize: '24px', color: 'var(--text-muted)' }}>→</div>
                <div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Realistic Savings</div>
                  <div style={{ fontSize: '20px', fontWeight: '800', color: 'var(--accent)' }}>{formatCurrency(realism.realistic_savings_inr)}</div>
                </div>
             </div>

             <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                {realism.risk_factors.map(risk => (
                  <span key={risk} style={{ background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', padding: '6px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: '500', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                    ⚠️ {risk.replace(/_/g, ' ')}
                  </span>
                ))}
             </div>
          </div>
        </div>

        {/* XAI Insights Section */}
        <div className="chart-container" style={{ gridColumn: 'span 1', height: 'auto', minHeight: '220px' }}>
          <div className="chart-header">
            <h3>Key Insights</h3>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 'bold' }}>AI GENERATED</div>
          </div>
          
          <div className="insights-list" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {insights.map((insight, i) => {
              const isIncrease = insight.direction === 'increase';
              const isDecrease = insight.direction === 'decrease';
              const iconColor = isIncrease ? 'var(--p-red-600)' : (isDecrease ? 'var(--p-green-600)' : 'var(--text-muted)');
              const iconBg = isIncrease ? 'var(--p-red-100)' : (isDecrease ? 'var(--p-green-100)' : 'var(--bg-main)');
              const icon = isIncrease ? '↑' : (isDecrease ? '↓' : '→');

              return (
                <div key={i} style={{ display: 'flex', gap: '16px', alignItems: 'flex-start', borderBottom: '1px solid var(--border)', paddingBottom: '12px' }}>
                  <div style={{ 
                    minWidth: '40px', padding: '4px 0', borderRadius: '4px', background: 'var(--bg-main)', border: '1px solid var(--border)',
                    textAlign: 'center', fontSize: '11px', fontWeight: 'bold', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column'
                  }}>
                    <span>{insight.time.split(' ')[0] || 'N/A'}</span>
                    <span>{insight.time.split(' ')[1] || ''}</span>
                  </div>
                  
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '14px', lineHeight: '1.4', marginBottom: '4px' }}>
                      {insight.explanation}
                    </div>
                    {insight.impact_percent > 0 && (
                      <div style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span style={{ 
                          background: iconBg, color: iconColor, width: '16px', height: '16px', borderRadius: '50%', 
                          display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', fontWeight: 'bold' 
                        }}>{icon}</span>
                        Primary driver impact: <span style={{ fontWeight: '600' }}>{insight.impact_percent.toFixed(0)}%</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

Insights.propTypes = {
  insights: PropTypes.array,
  realism: PropTypes.object
};