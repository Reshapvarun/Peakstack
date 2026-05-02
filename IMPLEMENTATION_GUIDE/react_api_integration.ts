"""
Task #5: React API Integration
TypeScript/JavaScript code for connecting React dashboard to FastAPI backend
"""

// File: src/api/peakstackApi.ts
// Production-ready API integration layer

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

interface AnalysisRequest {
  state: string;
  battery_kwh: number;
  battery_power_kw: number;
  solar_kw: number;
  annual_kwh?: number;
  load_profile?: number[];
}

interface AnalysisResponse {
  analysis_id: string;
  timestamp: string;
  state: string;
  battery_kwh: number;
  battery_power_kw: number;
  solar_kw: number;
  kpis: KPISchema;
  realism: RealismSchema;
  daily_chart: ChartData;
  yearly_chart?: ChartData;
  insights: InsightSchema[];
  recommendation: string;
  recommendation_reason: string;
  data_quality_score: number;
  data_quality_issues: string[];
}

interface KPISchema {
  monthly_savings_inr: number;
  annual_savings_inr: number;
  payback_years: number;
  payback_months: number;
  roi_percent: number;
  npv_10yr_inr: number;
  peak_demand_reduction_kw: number;
  peak_demand_reduction_percent: number;
}

interface RealismSchema {
  theoretical_savings_inr: number;
  realistic_savings_inr: number;
  realism_gap_percent: number;
  confidence_score: number;
  confidence_reason: string;
  risk_factors: string[];
  recommended_buffer_percent: number;
  conservative_estimate_inr: number;
}

interface ChartData {
  timestamps: string[];
  load_kw: number[];
  solar_generation_kw: number[];
  battery_charge_kw: number[];
  battery_discharge_kw: number[];
  battery_soc_percent: number[];
  grid_import_kw: number[];
  grid_import_without_bess_kw: number[];
}

interface InsightSchema {
  type: string;
  description: string;
  impact_inr: number;
  impact_percent: number;
}

// Task #5: API Function
export async function analyzeInvestment(
  request: AnalysisRequest,
  onProgress?: (stage: string) => void
): Promise<AnalysisResponse> {
  try {
    onProgress?.("Sending request to backend...");

    const response = await fetch(`${API_BASE}/api/v1/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(
        errorData.detail?.message || `API error: ${response.status}`
      );
    }

    onProgress?.("Processing results...");
    const data: AnalysisResponse = await response.json();

    onProgress?.("Complete!");
    return data;
  } catch (error) {
    console.error("Analysis failed:", error);
    throw error;
  }
}

// Task #5: Component Usage Example
export const ExampleComponentUsage = () => {
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [result, setResult] = React.useState<AnalysisResponse | null>(null);

  const handleAnalyze = async (inputs: AnalysisRequest) => {
    setLoading(true);
    setError(null);

    try {
      const response = await analyzeInvestment(inputs, (stage) => {
        console.log(`Progress: ${stage}`);
      });
      setResult(response);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unknown error occurred"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <AnalysisForm onSubmit={handleAnalyze} loading={loading} />
      {error && <ErrorBox message={error} />}
      {result && <AnalysisResults data={result} />}
    </div>
  );
};
