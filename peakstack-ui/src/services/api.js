/**
 * TASK #5: API Service for React Frontend
 * 
 * Connects React dashboard to FastAPI backend /analyze endpoint
 * Features:
 * - POST request with form inputs
 * - Response handling with state management
 * - Error handling and loading states
 * - Reusable across components
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

/**
 * Send analysis request to backend
 * @param {Object} params - Analysis parameters
 * @returns {Promise<Object>} - AnalysisResponse from API
 */
export async function analyzeEnergy(params) {
  const payload = {
    state: params.state,
    battery_kwh: parseFloat(params.battery_kwh),
    battery_power_kw: parseFloat(params.battery_power_kw),
    solar_kw: parseFloat(params.solar_kw),
    annual_kwh: params.annual_kwh ? parseFloat(params.annual_kwh) : null,
    load_profile: params.load_profile || null,
    analysis_name: params.analysis_name || null,
    tariff_energy: parseFloat(params.tariff_energy),
    demand_charge: parseFloat(params.demand_charge),
    peak_tariff_difference: parseFloat(params.peak_tariff_difference),
    battery_cost_per_kwh: parseFloat(params.battery_cost_per_kwh),
    solar_cost_per_kwh: parseFloat(params.solar_cost_per_kwh),
    utilization_factor: parseFloat(params.utilization_factor),
    industry: params.industry,
  };

  const response = await fetch(`${API_BASE_URL}/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Analysis failed');
  }

  return response.json();
}

/**
 * Get previously cached analysis
 * @param {string} analysisId - UUID of previous analysis
 * @returns {Promise<Object>} - AnalysisResponse
 */
export async function getAnalysis(analysisId) {
  const response = await fetch(`${API_BASE_URL}/analyses/${analysisId}`);
  if (!response.ok) {
    throw new Error('Analysis not found');
  }
  return response.json();
}

/**
 * Validate battery configuration
 * @param {Object} config - Battery config
 * @returns {Object} - { isValid: boolean, errors: [string] }
 */
export function validateBatteryConfig(config) {
  const errors = [];

  if (!config.battery_kwh || config.battery_kwh < 10 || config.battery_kwh > 2000) {
    errors.push('Battery capacity must be 10-2000 kWh');
  }

  if (!config.battery_power_kw || config.battery_power_kw < 1 || config.battery_power_kw > 500) {
    errors.push('Battery power must be 1-500 kW');
  }

  if (config.battery_power_kw > config.battery_kwh * 10) {
    errors.push('Battery power cannot exceed 10x capacity');
  }

  if (!config.state) {
    errors.push('State is required');
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

/**
 * Format currency (INR)
 * @param {number} value - Amount in rupees
 * @returns {string} - Formatted string
 */
export function formatCurrency(value) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

/**
 * Format percentage
 * @param {number} value - Decimal value
 * @returns {string} - Formatted percentage
 */
export function formatPercentage(value) {
  return `${(value * 100).toFixed(2)}%`;
}

export default {
  analyzeEnergy,
  getAnalysis,
  validateBatteryConfig,
  formatCurrency,
  formatPercentage,
};
