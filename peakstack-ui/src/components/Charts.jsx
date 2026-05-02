import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid,
  Line, Legend, ResponsiveContainer, ComposedChart, Cell
} from "recharts";
import { motion, AnimatePresence } from 'framer-motion';
import PropTypes from 'prop-types';

export default function Charts({ 
  dailyChart, 
  type = 'profile'
}) {
  const [replay, setReplay] = React.useState({ isPlaying: false, index: 0 });
  const [selectedPoint, setSelectedPoint] = React.useState(null);

  if (!dailyChart) return null;

  const dailyChartData = dailyChart.timestamps.map((time, i) => ({
    time: time,
    load: dailyChart.load_kw[i] || 0,
    solar: dailyChart.solar_generation_kw[i] || 0,
    battery_discharge: dailyChart.battery_discharge_kw[i] || 0,
    battery_charge: dailyChart.battery_charge_kw[i] || 0,
    grid_with_bess: dailyChart.grid_import_kw[i] || 0,
    grid_without_bess: dailyChart.grid_import_without_bess_kw?.[i] || 0,
    soc: dailyChart.battery_soc_percent?.[i] || 50,
    tariff: dailyChart.dg_offset_kw?.[i] || 0, // Reuse for demo or add field
  }));

  // Replay Logic
  React.useEffect(() => {
    let interval;
    if (replay.isPlaying) {
      interval = setInterval(() => {
        setReplay(prev => ({
          ...prev,
          index: (prev.index + 1) % dailyChartData.length
        }));
      }, 500);
    }
    return () => clearInterval(interval);
  }, [replay.isPlaying, dailyChartData.length]);

  if (type === 'comparison') {
    // ... (keep comparison logic)
    const withoutBessTotal = dailyChartData.reduce((acc, curr) => acc + curr.grid_without_bess, 0) / 4;
    const withBessTotal = dailyChartData.reduce((acc, curr) => acc + curr.grid_with_bess, 0) / 4;
    const comparisonData = [
      { name: 'Without BESS', value: withoutBessTotal, fill: '#94a3b8' },
      { name: 'With BESS', value: withBessTotal, fill: '#10b981' }
    ];
    return (
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={comparisonData} margin={{ top: 10, right: 20, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
          <XAxis dataKey="name" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
          <YAxis tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
          <Tooltip 
            formatter={(value) => `₹${(value * 8).toLocaleString()}`}
            contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }}
          />
          <Bar dataKey="value" barSize={80} radius={[6, 6, 0, 0]}>
            {comparisonData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    );
  }

  const currentData = replay.isPlaying ? dailyChartData[replay.index] : null;

  return (
    <div style={{ position: 'relative' }}>
      {/* Replay Controls (Req #10) */}
      <div className="chart-header" style={{ marginBottom: 10 }}>
        <button 
          className="btn-ghost" 
          onClick={() => setReplay(p => ({ ...p, isPlaying: !p.isPlaying }))}
          style={{ padding: '2px 10px', fontSize: 10 }}
        >
          {replay.isPlaying ? '⏸ Pause Replay' : '▶ Play Replay'}
        </button>
        {replay.isPlaying && (
          <span style={{ fontSize: 10, color: 'var(--accent)' }}>
            Replaying: {currentData?.time} | SOC: {currentData?.soc.toFixed(1)}%
          </span>
        )}
      </div>

      <ResponsiveContainer width="100%" height={260}>
        <ComposedChart 
          data={dailyChartData} 
          margin={{ top: 10, right: 20, left: 10, bottom: 5 }}
          onClick={(data) => data && setSelectedPoint(data.activePayload?.[0]?.payload)}
        >
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
          <XAxis dataKey="time" interval={11} tick={{ fontSize: 10, fill: 'var(--text-muted)' }} />
          <YAxis yAxisId="power" domain={['auto', 'auto']} tick={{ fontSize: 10, fill: 'var(--text-muted)' }} />
          <YAxis yAxisId="soc" orientation="right" domain={[0, 100]} tick={{ fontSize: 10, fill: 'var(--text-muted)' }} />
          <Tooltip 
            contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }}
          />
          <Legend wrapperStyle={{ paddingTop: '6px', fontSize: 11 }} iconType="square" />
          
          <Bar yAxisId="power" dataKey="battery_charge" fill="#10b981" opacity={0.85} name="Charge" />
          <Bar yAxisId="power" dataKey="battery_discharge" fill="#ef4444" opacity={0.85} name="Discharge" />
          <Line yAxisId="soc" type="monotone" dataKey="soc" stroke="#2563eb" strokeWidth={2.5} dot={false} name="SOC" />
          
          {/* Replay Highlight */}
          {replay.isPlaying && (
            <Line yAxisId="soc" data={[{ time: currentData?.time, soc: currentData?.soc }]} dataKey="soc" stroke="orange" strokeWidth={5} dot={{ r: 8 }} />
          )}
        </ComposedChart>
      </ResponsiveContainer>

      {/* Interval Insight Modal (Req #9) */}
      <AnimatePresence>
        {selectedPoint && (
          <motion.div 
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            style={{ 
              position: 'absolute', top: 40, right: 20, width: 200, 
              background: 'var(--bg-card)', border: '2px solid var(--accent)', 
              borderRadius: 8, padding: 12, zIndex: 100, boxShadow: 'var(--shadow)'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <strong style={{ fontSize: 12 }}>{selectedPoint.time} Insight</strong>
              <button onClick={() => setSelectedPoint(null)} style={{ border: 'none', background: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>✕</button>
            </div>
            <div style={{ fontSize: 11, display: 'flex', flexDirection: 'column', gap: 4 }}>
              <div>💰 Price: ₹{selectedPoint.tariff?.toFixed(2) || '8.50'}/kWh</div>
              <div>🏠 Load: {selectedPoint.load.toFixed(1)} kW</div>
              <div>☀️ Solar: {selectedPoint.solar.toFixed(1)} kW</div>
              <div style={{ marginTop: 4, color: 'var(--accent)', fontWeight: 600 }}>
                Reason: {selectedPoint.battery_discharge < 0 ? 'Peak Shaving' : selectedPoint.battery_charge > 0 ? 'Solar Charging' : 'Optimal Idle'}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

Charts.propTypes = {
  dailyChart: PropTypes.object,
  type: PropTypes.string
};