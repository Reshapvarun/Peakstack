"""
Task #6, #7, #8: React Components
Dynamic charts, insights, and realism gap display
Remove all hardcoded values, make everything data-driven
"""

// File: src/components/AnalysisResults.tsx

import React, { useState } from "react";
import { LineChart, BarChart, PieChart, Card, Statistic, Spin, Alert } from "antd";
import { ArrowUpOutlined, ArrowDownOutlined } from "@ant-design/icons";
import type { AnalysisResponse } from "../api/peakstackApi";

// ============= TASK #6: DYNAMIC CHARTS =============

interface ChartsProps {
  data: AnalysisResponse;
}

/**
 * Task #6: Charts Component
 * Remove hardcoded data, accept props from API response
 * Render dynamic charts using Recharts
 */
export const DynamicCharts: React.FC<ChartsProps> = ({ data }) => {
  const [timeframe, setTimeframe] = useState<"day" | "year">("day");

  // Get active chart data
  const chartData =
    timeframe === "day" ? data.daily_chart : data.yearly_chart || data.daily_chart;

  if (!chartData) {
    return <Alert type="warning" message="No chart data available" />;
  }

  // Prepare Recharts data
  const rechartsData = chartData.timestamps.map((timestamp, i) => ({
    timestamp,
    load: chartData.load_kw[i] || 0,
    solar: chartData.solar_generation_kw[i] || 0,
    battery_charge: chartData.battery_charge_kw[i] || 0,
    battery_discharge: chartData.battery_discharge_kw[i] || 0,
    soc: chartData.battery_soc_percent[i] || 0,
    grid_with_bess: chartData.grid_import_kw[i] || 0,
    grid_without_bess: chartData.grid_import_without_bess_kw[i] || 0,
  }));

  return (
    <div className="charts-container">
      <div className="tabs">
        <button
          className={timeframe === "day" ? "active" : ""}
          onClick={() => setTimeframe("day")}
        >
          Daily Profile
        </button>
        <button
          className={timeframe === "year" ? "active" : ""}
          onClick={() => setTimeframe("year")}
        >
          Yearly Profile
        </button>
      </div>

      {/* Chart 1: Load Profile with Solar */}
      <Card title="Load & Solar Generation Profile">
        {rechartsData.length === 0 ? (
          <Alert type="warning" message="No data to display" />
        ) : (
          <LineChart width={800} height={400} data={rechartsData}>
            <CartesianGrid />
            <XAxis dataKey="timestamp" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="load" stroke="#8884d8" name="Load (kW)" />
            <Line
              type="monotone"
              dataKey="solar"
              stroke="#82ca9d"
              name="Solar (kW)"
            />
          </LineChart>
        )}
      </Card>

      {/* Chart 2: Battery Dispatch & SOC */}
      <Card title="Battery Charge/Discharge & State of Charge">
        {rechartsData.length === 0 ? (
          <Alert type="warning" message="No data to display" />
        ) : (
          <ComposedChart width={800} height={400} data={rechartsData}>
            <CartesianGrid />
            <XAxis dataKey="timestamp" />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend />
            <Bar
              yAxisId="left"
              dataKey="battery_charge"
              fill="#0066cc"
              name="Charging (kW)"
            />
            <Bar
              yAxisId="left"
              dataKey="battery_discharge"
              fill="#ff6600"
              name="Discharging (kW)"
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="soc"
              stroke="#666"
              name="SOC (%)"
            />
          </ComposedChart>
        )}
      </Card>

      {/* Chart 3: Grid Import Comparison (WITH vs WITHOUT BESS) */}
      <Card title="Grid Import Comparison: With BESS vs Without">
        {rechartsData.length === 0 ? (
          <Alert type="warning" message="No data to display" />
        ) : (
          <LineChart width={800} height={400} data={rechartsData}>
            <CartesianGrid />
            <XAxis dataKey="timestamp" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="grid_without_bess"
              stroke="#cc0000"
              name="Without BESS (Baseline)"
              strokeDasharray="5 5"
            />
            <Line
              type="monotone"
              dataKey="grid_with_bess"
              stroke="#00cc00"
              name="With BESS (Optimized)"
            />
          </LineChart>
        )}
      </Card>
    </div>
  );
};

// ============= TASK #7: DYNAMIC INSIGHTS =============

interface InsightsProps {
  data: AnalysisResponse;
}

/**
 * Task #7: Insights Component
 * Generate insights from API response, not static text
 */
export const DynamicInsights: React.FC<InsightsProps> = ({ data }) => {
  if (!data.insights || data.insights.length === 0) {
    return <Alert type="info" message="No insights available" />;
  }

  return (
    <div className="insights-container">
      <h2>💡 Business Insights (XAI)</h2>

      {data.insights.map((insight, idx) => (
        <Card key={idx} className="insight-card">
          {/* Icon based on insight type */}
          <div className="insight-header">
            <span className="insight-type">
              {insight.type === "peak_shaving" && "🎯"}
              {insight.type === "arbitrage" && "💰"}
              {insight.type === "solar_buffering" && "☀️"}
              {insight.type === "demand_response" && "⚡"}
            </span>
            <h3>{_formatInsightType(insight.type)}</h3>
          </div>

          <p className="insight-description">{insight.description}</p>

          <div className="insight-metrics">
            <Statistic
              title="Annual Impact"
              value={insight.impact_inr}
              prefix="₹"
              suffix="/year"
            />
            <Statistic
              title="Share of Total"
              value={insight.impact_percent}
              suffix="%"
            />
          </div>
        </Card>
      ))}
    </div>
  );
};

function _formatInsightType(type: string): string {
  const types: Record<string, string> = {
    peak_shaving: "Peak Shaving",
    arbitrage: "Energy Arbitrage",
    solar_buffering: "Solar Buffering",
    demand_response: "Demand Response",
  };
  return types[type] || type;
}

// ============= TASK #8: REALISM GAP FEATURE =============

interface RealismGapProps {
  data: AnalysisResponse;
}

/**
 * Task #8: Realism Gap Feature
 * Differentiator: Shows confidence + risk factors + conservative estimate
 * Investor-demo ready
 */
export const RealismGapCard: React.FC<RealismGapProps> = ({ data }) => {
  const { realism } = data;

  // Determine gap severity color
  const getGapColor = (gap: number) => {
    if (gap < 10) return "#00cc00"; // Green: low gap
    if (gap < 25) return "#ffaa00"; // Yellow: moderate gap
    return "#cc0000"; // Red: high gap
  };

  // Confidence level text
  const getConfidenceText = (score: number) => {
    if (score >= 0.85) return "🟢 High";
    if (score >= 0.70) return "🟡 Moderate";
    return "🔴 Low";
  };

  return (
    <Card className="realism-card" title="Realism Calibration & Confidence">
      <div className="realism-grid">
        {/* Left: Savings Comparison */}
        <div className="realism-column">
          <h3>Savings Estimates</h3>

          <div className="savings-box theoretical">
            <div className="label">Theoretical (Model)</div>
            <div className="value">
              ₹{_formatNumber(realism.theoretical_savings_inr)}
            </div>
            <div className="note">Ideal conditions, no real-world constraints</div>
          </div>

          <div className="arrow">↓</div>

          <div className="savings-box realistic">
            <div className="label">Realistic (XAI-Calibrated)</div>
            <div className="value">
              ₹{_formatNumber(realism.realistic_savings_inr)}
            </div>
            <div className="note">Accounts for state tariffs & real-world factors</div>
          </div>

          <div className="realism-gap">
            <div
              className="gap-bar"
              style={{
                width: `${Math.min(realism.realism_gap_percent, 100)}%`,
                backgroundColor: getGapColor(realism.realism_gap_percent),
              }}
            />
            <div className="gap-text">
              Gap: {realism.realism_gap_percent.toFixed(1)}%
            </div>
          </div>

          {realism.realism_gap_percent > 30 && (
            <Alert
              type="warning"
              message="Large realism gap detected"
              description="This estimate differs significantly from theoretical. See risk factors below."
            />
          )}
        </div>

        {/* Right: Confidence & Risks */}
        <div className="realism-column">
          <h3>Confidence & Risks</h3>

          <Card className="confidence-box">
            <div className="confidence-score">
              <div className="score-circle">
                {(realism.confidence_score * 100).toFixed(0)}%
              </div>
              <div className="score-label">
                Confidence: {getConfidenceText(realism.confidence_score)}
              </div>
            </div>

            <p className="confidence-reason">{realism.confidence_reason}</p>
          </Card>

          {/* Risk Factors */}
          {realism.risk_factors.length > 0 && (
            <div className="risk-factors">
              <h4>Risk Factors Identified:</h4>
              {realism.risk_factors.map((risk, idx) => (
                <div key={idx} className="risk-factor">
                  ⚠️ {_formatRiskName(risk)}
                </div>
              ))}
            </div>
          )}

          {/* Conservative Estimate */}
          <Card className="conservative-box">
            <div className="label">Conservative Estimate</div>
            <div className="value">
              ₹{_formatNumber(realism.conservative_estimate_inr)}
            </div>
            <div className="formula">
              = Realistic × (1 - {realism.recommended_buffer_percent}% buffer)
            </div>
            <div className="note">
              Use this for risk-averse investment decisions
            </div>
          </Card>
        </div>
      </div>

      {/* Investor Pitch */}
      <div className="investor-pitch">
        <h4>💼 Investor Summary</h4>
        <p>
          <strong>Honest Estimate:</strong> ₹
          {_formatNumber(realism.conservative_estimate_inr)}/year
        </p>
        <p>
          <strong>Confidence:</strong> {(realism.confidence_score * 100).toFixed(0)}%
        </p>
        <p>
          <strong>Why?</strong> {realism.confidence_reason}
        </p>
      </div>
    </Card>
  );
};

function _formatNumber(num: number): string {
  return num.toLocaleString("en-IN", { maximumFractionDigits: 0 });
}

function _formatRiskName(risk: string): string {
  return risk
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

// ============= KPI CARDS =============

interface KPICardsProps {
  data: AnalysisResponse;
}

export const KPICards: React.FC<KPICardsProps> = ({ data }) => {
  const { kpis, realism } = data;

  return (
    <div className="kpi-grid">
      <Card>
        <Statistic
          title="Annual Savings"
          value={kpis.annual_savings_inr}
          prefix="₹"
          valueStyle={{ color: "#00aa00" }}
        />
        <div className="note">Realistic: ₹{_formatNumber(realism.realistic_savings_inr)}</div>
      </Card>

      <Card>
        <Statistic
          title="Payback Period"
          value={kpis.payback_years}
          suffix="years"
          valueStyle={{ color: kpis.payback_years < 7 ? "#00aa00" : "#ff6600" }}
        />
      </Card>

      <Card>
        <Statistic
          title="ROI (Annual)"
          value={kpis.roi_percent}
          suffix="%"
          valueStyle={{ color: kpis.roi_percent > 10 ? "#00aa00" : "#ff6600" }}
        />
      </Card>

      <Card>
        <Statistic
          title="Peak Reduction"
          value={kpis.peak_demand_reduction_kw}
          suffix="kW"
        />
      </Card>

      <Card>
        <Statistic
          title="10-Year NPV"
          value={kpis.npv_10yr_inr}
          prefix="₹"
          valueStyle={{ color: "#0066cc" }}
        />
      </Card>

      <Card>
        <Statistic
          title="Confidence Score"
          value={realism.confidence_score}
          suffix={`/1`}
          precision={2}
          valueStyle={{ color: realism.confidence_score > 0.8 ? "#00aa00" : "#ff6600" }}
        />
      </Card>
    </div>
  );
};

// ============= RECOMMENDATION CARD =============

interface RecommendationProps {
  data: AnalysisResponse;
}

export const RecommendationCard: React.FC<RecommendationProps> = ({ data }) => {
  const { recommendation, recommendation_reason } = data;

  const getRecommendationColor = () => {
    if (recommendation === "INSTALL") return "#00cc00";
    if (recommendation === "DO_NOT_INSTALL") return "#cc0000";
    return "#ffaa00";
  };

  const getRecommendationIcon = () => {
    if (recommendation === "INSTALL") return "✅";
    if (recommendation === "DO_NOT_INSTALL") return "❌";
    return "⚠️";
  };

  return (
    <Card
      title="Recommendation"
      style={{ borderLeft: `4px solid ${getRecommendationColor()}` }}
    >
      <div className="recommendation-box">
        <div className="recommendation-icon">
          {getRecommendationIcon()}
        </div>
        <div className="recommendation-content">
          <h2 style={{ color: getRecommendationColor() }}>
            {recommendation}
          </h2>
          <p>{recommendation_reason}</p>
        </div>
      </div>
    </Card>
  );
};

// ============= COMPLETE ANALYSIS RESULTS COMPONENT =============

interface AnalysisResultsProps {
  data: AnalysisResponse;
  loading?: boolean;
}

export const AnalysisResults: React.FC<AnalysisResultsProps> = ({
  data,
  loading = false,
}) => {
  if (loading) {
    return <Spin size="large" />;
  }

  return (
    <div className="analysis-results">
      <div className="header">
        <h1>BESS Investment Analysis Results</h1>
        <div className="metadata">
          <span>Analysis ID: {data.analysis_id}</span>
          <span>State: {data.state.toUpperCase()}</span>
          <span>Battery: {data.battery_kwh} kWh</span>
        </div>
      </div>

      {/* KPI Summary */}
      <KPICards data={data} />

      {/* Recommendation (Prominent) */}
      <RecommendationCard data={data} />

      {/* Realism Gap (Your Moat) */}
      <RealismGapCard data={data} />

      {/* Dynamic Charts */}
      <DynamicCharts data={data} />

      {/* Insights */}
      <DynamicInsights data={data} />

      {/* Data Quality */}
      {data.data_quality_issues.length > 0 && (
        <Alert
          type="info"
          message="Data Quality Notes"
          description={data.data_quality_issues.join(", ")}
        />
      )}
    </div>
  );
};
