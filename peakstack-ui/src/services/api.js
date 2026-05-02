/**
 * TASK: API Service for React Frontend
 * Hardened for production with robust parsing and job polling
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

/**
 * Robust response parsing helper
 */
async function parseResponse(res) {
  const text = await res.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch (e) {
    throw new Error(`Server Error: ${text || res.statusText}`);
  }
  
  if (!res.ok) {
    throw new Error(data.detail || data.error || 'Request failed');
  }
  return data;
}

/**
 * Send analysis request to backend (returns job_id)
 * @param {Object} params - Analysis parameters
 * @returns {Promise<Object>} - { job_id: string, status: string }
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
    dg_cost_per_kwh: parseFloat(params.dg_cost_per_kwh || 20.0),
    dg_hours_per_day: parseFloat(params.dg_hours_per_day || 2.0),
    horizon_days: parseInt(params.horizon_days || 1),
    csv_file_id: params.csv_file_id || null,
    use_real_data: !!params.use_real_data,
  };
  
  console.log("[API] Sending Analysis Payload:", payload);

  const res = await fetch(`${API_BASE_URL}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  return parseResponse(res);
}

/**
 * Poll job status until completion
 * @param {number} jobId - Job ID
 */
export async function pollJob(jobId, onProgress) {
  const maxRetries = 100; // ~5 minutes with 3s interval
  let retries = 0;
  
  while (retries < maxRetries) {
    try {
      const res = await fetch(`${API_BASE_URL}/jobs/${jobId}`);
      if (!res.ok) {
         // If server is temporarily overloaded, don't crash the loop
         if (res.status === 503 || res.status === 502) {
           await new Promise(r => setTimeout(r, 5000));
           continue;
         }
         throw new Error(`Polling failed: ${res.statusText}`);
      }
      
      const data = await res.json();
      
      if (data.status === 'completed') return data.results;
      if (data.status === 'failed') throw new Error(data.error || 'Analysis job failed on server.');
      
      if (onProgress) onProgress(data.status);
    } catch (err) {
      console.warn("Polling error (retrying):", err);
      if (retries > 10 && err.message.includes('Failed to fetch')) {
         throw new Error('Connection lost. Please check if the server is running.');
      }
    }
    
    await new Promise(r => setTimeout(r, 3000));
    retries++;
  }
  throw new Error('Analysis timed out. The system might be under heavy load.');
}

/**
 * Get previously cached analysis
 */
export async function getAnalysis(analysisId) {
  const res = await fetch(`${API_BASE_URL}/analyses/${analysisId}`);
  return parseResponse(res);
}

/**
 * Format currency (INR)
 */
export function formatCurrency(value) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export default {
  analyzeEnergy,
  pollJob,
  getAnalysis,
  formatCurrency,
};

