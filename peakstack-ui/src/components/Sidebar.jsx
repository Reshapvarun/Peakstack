import React from 'react';
import { motion } from 'framer-motion';

export default function Sidebar({ inputs, updateInput, loading, onAnalyze }) {
  const {
    state, industry, battery_kwh, battery_power_kw, solar_kw, annual_kwh,
    tariff_energy, demand_charge, peak_tariff_difference,
    battery_cost_per_kwh, solar_cost_per_kwh, utilization_factor,
  } = inputs;

  const STATES = [
    { id: 'maharashtra', name: 'Maharashtra' },
    { id: 'karnataka',   name: 'Karnataka'   },
    { id: 'tamil_nadu',  name: 'Tamil Nadu'  },
    { id: 'delhi',       name: 'Delhi'       },
    { id: 'rajasthan',   name: 'Rajasthan'   },
    { id: 'gujarat',     name: 'Gujarat'     },
  ];

  const applyScenario = (overrides) =>
    Object.entries(overrides).forEach(([k, v]) => updateInput(k, v));

  return (
    <motion.aside
      className="sidebar"
      initial={{ x: -320 }}
      animate={{ x: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
    >
      {/* Logo */}
      <div className="logo-section">
        <img src="/src/assets/logo.png" className="logo-img" alt="Peakstack" />
      </div>

      {/* ── Location & Industry ── */}
      <div className="sidebar-group">
        <h3>Location &amp; Industry</h3>

        <label className="sidebar-label">State / UT</label>
        <select
          value={state}
          onChange={e => updateInput('state', e.target.value)}
          disabled={loading}
        >
          {STATES.map(s => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>

        <label className="sidebar-label">Industry Type</label>
        <select
          value={industry}
          onChange={e => updateInput('industry', e.target.value)}
          disabled={loading}
        >
          <option value="manufacturing">Manufacturing (1.8× peak)</option>
          <option value="commercial">Commercial (1.3× peak)</option>
          <option value="hospitality">Hospitality (1.3× peak)</option>
          <option value="other">Other (1.3× peak)</option>
        </select>
      </div>

      {/* ── Quick Scenarios ── */}
      <div className="sidebar-group">
        <h3>Quick Scenarios</h3>
        <div className="quick-scenarios">
          <button
            className="scenario-btn"
            disabled={loading}
            onClick={() => applyScenario({
              battery_kwh: 1000, battery_power_kw: 500,
              solar_kw: 500, demand_charge: 450,
              industry: 'manufacturing',
            })}
          >🏭 High Peak Factory</button>

          <button
            className="scenario-btn"
            disabled={loading}
            onClick={() => applyScenario({
              battery_kwh: 400, battery_power_kw: 200,
              solar_kw: 800, peak_tariff_difference: 4.5,
              state: 'tamil_nadu',
            })}
          >☀️ Solar Rich Plant</button>

          <button
            className="scenario-btn"
            disabled={loading}
            onClick={() => applyScenario({
              battery_kwh: 250, battery_power_kw: 100,
              solar_kw: 100, tariff_energy: 10,
              industry: 'commercial',
            })}
          >🏢 Commercial Site</button>
        </div>
      </div>

      {/* ── System Parameters ── */}
      <div className="sidebar-group">
        <h3>System Parameters</h3>

        <SliderRow
          label="Battery Capacity" val={`${battery_kwh} kWh`}
          min={100} max={2000} step={50} value={battery_kwh}
          onChange={v => updateInput('battery_kwh', +v)} disabled={loading}
        />
        <SliderRow
          label="Battery Power" val={`${battery_power_kw} kW`}
          min={50} max={1000} step={10} value={battery_power_kw}
          onChange={v => updateInput('battery_power_kw', +v)} disabled={loading}
        />
        <SliderRow
          label="Solar Capacity" val={`${solar_kw} kW`}
          min={0} max={2000} step={50} value={solar_kw}
          onChange={v => updateInput('solar_kw', +v)} disabled={loading}
        />
        <SliderRow
          label="Annual Consumption" val={`${Math.round(annual_kwh / 1000)}k kWh`}
          min={100000} max={5000000} step={50000} value={annual_kwh}
          onChange={v => updateInput('annual_kwh', +v)} disabled={loading}
        />
        <SliderRow
          label="Utilisation Factor" val={`${(utilization_factor * 100).toFixed(0)}%`}
          min={0.5} max={1.0} step={0.05} value={utilization_factor}
          onChange={v => updateInput('utilization_factor', +v)} disabled={loading}
        />
      </div>

      {/* ── Financial Inputs ── */}
      <div className="sidebar-group">
        <h3>Financial Inputs</h3>

        <SliderRow
          label="Base Tariff" val={`₹${tariff_energy}/kWh`}
          min={4} max={15} step={0.5} value={tariff_energy}
          onChange={v => updateInput('tariff_energy', +v)} disabled={loading}
        />
        <SliderRow
          label="Peak Delta" val={`₹${peak_tariff_difference}/kWh`}
          min={0} max={8} step={0.1} value={peak_tariff_difference}
          onChange={v => updateInput('peak_tariff_difference', +v)} disabled={loading}
        />
        <SliderRow
          label="Demand Charge" val={`₹${demand_charge}/kVA`}
          min={100} max={1000} step={10} value={demand_charge}
          onChange={v => updateInput('demand_charge', +v)} disabled={loading}
        />
        <SliderRow
          label="Solar LCOE" val={`₹${Number(solar_cost_per_kwh).toFixed(1)}/kWh`}
          min={2.5} max={6.0} step={0.1} value={solar_cost_per_kwh}
          onChange={v => updateInput('solar_cost_per_kwh', +v)} disabled={loading}
        />
        <SliderRow
          label="BESS CapEx / kWh" val={`₹${Number(battery_cost_per_kwh).toLocaleString('en-IN')}`}
          min={10000} max={40000} step={500} value={battery_cost_per_kwh}
          onChange={v => updateInput('battery_cost_per_kwh', +v)} disabled={loading}
        />
      </div>

      {/* Analyze button — sticks to bottom */}
      <button
        className="btn-analyze"
        onClick={onAnalyze}
        disabled={loading}
      >
        {loading ? '⏳ Analyzing…' : '▶ Run Investment Analysis'}
      </button>
    </motion.aside>
  );
}

/* ── Reusable slider row ── */
function SliderRow({ label, val, min, max, step, value, onChange, disabled }) {
  return (
    <div className="range-group">
      <div className="range-header">
        <span className="sidebar-label" style={{ marginBottom: 0 }}>{label}</span>
        <span className="range-val">{val}</span>
      </div>
      <input
        type="range"
        min={min} max={max} step={step} value={value}
        onChange={e => onChange(e.target.value)}
        disabled={disabled}
      />
    </div>
  );
}