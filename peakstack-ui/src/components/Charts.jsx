import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid,
  Line, Legend, ResponsiveContainer, ComposedChart, Cell
} from "recharts";
import PropTypes from 'prop-types';

export default function Charts({ 
  dailyChart, 
  type = 'profile'
}) {
  if (!dailyChart) return null;

  const dailyChartData = dailyChart.timestamps.map((time, i) => ({
    time: time.split(' ')[1] || time,
    load: dailyChart.load_kw[i] || 0,
    solar: dailyChart.solar_generation_kw[i] || 0,
    battery_discharge: -(dailyChart.battery_discharge_kw[i] || 0),
    battery_charge: dailyChart.battery_charge_kw[i] || 0,
    grid_with_bess: dailyChart.grid_import_kw[i] || 0,
    grid_without_bess: dailyChart.grid_import_without_bess_kw?.[i] || 0,
    soc: dailyChart.battery_soc_percent?.[i] || 50,
  }));

  /* ── Monthly Cost Comparison (Bar Chart) ── */
  if (type === 'comparison') {
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

  /* ── Dispatch Profile (ComposedChart: Charge/Discharge Bars + SOC Line) ── */
  return (
    <ResponsiveContainer width="100%" height={260}>
      <ComposedChart data={dailyChartData} margin={{ top: 10, right: 20, left: 10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
        <XAxis 
          dataKey="time" 
          interval={3} 
          tick={{ fontSize: 10, fill: 'var(--text-muted)' }} 
        />
        {/* Left Y-axis: Power (kW) */}
        <YAxis 
          yAxisId="power"
          tick={{ fontSize: 10, fill: 'var(--text-muted)' }}
          label={{ value: 'kW', angle: -90, position: 'insideLeft', style: { fontSize: 10, fill: 'var(--text-muted)' } }}
        />
        {/* Right Y-axis: SOC (%) */}
        <YAxis 
          yAxisId="soc"
          orientation="right"
          domain={[0, 100]}
          tick={{ fontSize: 10, fill: 'var(--text-muted)' }}
          label={{ value: 'SOC %', angle: 90, position: 'insideRight', style: { fontSize: 10, fill: 'var(--text-muted)' } }}
        />
        <Tooltip 
          contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }}
          formatter={(value, name) => {
            if (name === 'SOC') return [`${value.toFixed(0)}%`, name];
            return [`${Math.abs(value).toFixed(1)} kW`, name];
          }}
        />
        <Legend 
          wrapperStyle={{ paddingTop: '6px', fontSize: 11 }}
          iconType="square"
        />
        
        {/* Charge bars (positive, green) */}
        <Bar 
          yAxisId="power"
          dataKey="battery_charge" 
          fill="#10b981" 
          opacity={0.85} 
          name="Charge"
          radius={[2, 2, 0, 0]}
        />
        {/* Discharge bars (negative, red) */}
        <Bar 
          yAxisId="power"
          dataKey="battery_discharge" 
          fill="#ef4444" 
          opacity={0.85} 
          name="Discharge"
          radius={[0, 0, 2, 2]}
        />
        {/* SOC line on right axis */}
        <Line 
          yAxisId="soc"
          type="monotone" 
          dataKey="soc" 
          stroke="#6366f1" 
          strokeWidth={2.5} 
          dot={false} 
          name="SOC"
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

Charts.propTypes = {
  dailyChart: PropTypes.object,
  type: PropTypes.string
};