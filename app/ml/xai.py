import numpy as np
import pandas as pd
from datetime import datetime

class ExplainableAI:
    """
    Enterprise XAI Engine for the EMS.
    Upgraded for Phase 3: Multi-point SHAP analysis, temporal context, and correct normalization.
    """
    def __init__(self):
        pass

    def _format_feature_name(self, feat):
        feat_clean = feat.replace('_', ' ').title()
        if 'Lag' in feat_clean:
            feat_clean = feat_clean.replace('Lag ', 'Recent ') + ' Trend'
        if 'Ghi' in feat_clean:
            feat_clean = "Solar Irradiance (GHI)"
        return feat_clean

    def explain_forecast_batch(self, load_explainer, load_model, solar_explainer, solar_model, features_df):
        """
        Uses cached SHAP explainers to extract multi-point insights:
        - Top 3 load peaks
        - 1 median/normal hour
        - 1 solar dip (if applicable)
        """
        if load_explainer is None or solar_explainer is None:
            return {"insights": [], "confidence_score": 0.0, "error": "SHAP explainers not cached"}
            
        try:
            # 1. Generate Predictions for the full 96 steps
            load_preds = load_model.predict(features_df[[
                'hour', 'day_of_week', 'month', 'load_lag_15m', 'load_lag_1h', 'load_lag_24h', 'load_rolling_3h', 'temperature_c'
            ]])
            solar_preds = solar_model.predict(features_df[[
                'hour', 'month', 'solar_lag_15m', 'solar_lag_1h', 'solar_lag_24h', 'solar_rolling_3h', 'temperature_c', 'ghi'
            ]])
            
            # Ensure predictions are strictly positive
            load_preds = np.maximum(load_preds, 0)
            solar_preds = np.maximum(solar_preds, 0)

            # 2. Identify Points of Interest
            indices_to_explain = []
            
            # Top 3 Load Peaks
            top_3_indices = np.argsort(load_preds)[-3:][::-1]
            for idx in top_3_indices:
                indices_to_explain.append({'idx': idx, 'type': 'peak', 'model': 'load'})
                
            # 1 Normal Hour (closest to median)
            median_val = np.median(load_preds)
            median_idx = np.abs(load_preds - median_val).argmin()
            indices_to_explain.append({'idx': median_idx, 'type': 'normal', 'model': 'load'})
            
            # 1 Solar Dip (lowest solar during daylight 10:00 - 14:00)
            hours = features_df['hour'].values
            daylight_indices = np.where((hours >= 10) & (hours <= 14))[0]
            if len(daylight_indices) > 0:
                daylight_solar = solar_preds[daylight_indices]
                dip_idx_in_daylight = np.argmin(daylight_solar)
                solar_dip_idx = daylight_indices[dip_idx_in_daylight]
                indices_to_explain.append({'idx': solar_dip_idx, 'type': 'solar_dip', 'model': 'solar'})

            # 3. Batch SHAP Calculation
            # It's faster to calculate SHAP for the whole dataframe or just the selected indices.
            # We'll calculate for the whole dataframe for simplicity and subset.
            load_shap_values = load_explainer.shap_values(features_df[[
                'hour', 'day_of_week', 'month', 'load_lag_15m', 'load_lag_1h', 'load_lag_24h', 'load_rolling_3h', 'temperature_c'
            ]])
            solar_shap_values = solar_explainer.shap_values(features_df[[
                'hour', 'month', 'solar_lag_15m', 'solar_lag_1h', 'solar_lag_24h', 'solar_rolling_3h', 'temperature_c', 'ghi'
            ]])
            
            load_feature_names = ['hour', 'day_of_week', 'month', 'load_lag_15m', 'load_lag_1h', 'load_lag_24h', 'load_rolling_3h', 'temperature_c']
            solar_feature_names = ['hour', 'month', 'solar_lag_15m', 'solar_lag_1h', 'solar_lag_24h', 'solar_rolling_3h', 'temperature_c', 'ghi']

            # Baselines
            load_baseline = np.mean(load_preds)
            solar_baseline = np.mean(solar_preds[np.where((hours >= 6) & (hours <= 18))]) if np.any((hours >= 6) & (hours <= 18)) else 0.1
            
            insights = []
            
            # 4. Generate Structured Explanations
            for item in indices_to_explain:
                idx = item['idx']
                
                # Get timestamp for temporal context
                ts = pd.to_datetime(features_df.iloc[idx]['timestamp'])
                time_str = ts.strftime("%I:%M %p")
                
                if item['model'] == 'load':
                    pred_val = load_preds[idx]
                    shap_vals = load_shap_values[idx]
                    feat_names = load_feature_names
                    pct_change = ((pred_val - load_baseline) / load_baseline) * 100 if load_baseline > 0 else 0
                    base_str = "Load"
                else:
                    pred_val = solar_preds[idx]
                    shap_vals = solar_shap_values[idx]
                    feat_names = solar_feature_names
                    pct_change = ((pred_val - solar_baseline) / solar_baseline) * 100 if solar_baseline > 0 else 0
                    base_str = "Solar generation"

                # Mathematical Normalization
                total_abs_shap = np.sum(np.abs(shap_vals))
                
                # Sort features by impact
                impacts = [(feat_names[i], shap_vals[i]) for i in range(len(feat_names))]
                impacts.sort(key=lambda x: abs(x[1]), reverse=True)
                
                top_2 = impacts[:2]
                explanation_parts = []
                
                primary_impact_percent = 0
                for i, (feat, val) in enumerate(top_2):
                    pct = (abs(val) / total_abs_shap) * 100 if total_abs_shap > 0 else 0
                    if i == 0: primary_impact_percent = pct
                    
                    feat_clean = self._format_feature_name(feat)
                    
                    # Add context for temperature
                    if feat == 'temperature_c':
                        temp_val = features_df.iloc[idx]['temperature_c']
                        feat_clean += f" ({temp_val:.0f}°C)"
                        
                    explanation_parts.append(f"{feat_clean}")

                driver_str = " and ".join(explanation_parts)
                
                direction_verb = "increased" if pct_change > 0 else "decreased"
                
                if item['type'] == 'peak':
                    explanation = f"{base_str} {direction_verb} by {abs(pct_change):.0f}% at {time_str} primarily due to {driver_str}."
                    direction_flag = "increase"
                elif item['type'] == 'normal':
                    explanation = f"Steady state {base_str.lower()} at {time_str} driven by {driver_str}."
                    direction_flag = "neutral"
                elif item['type'] == 'solar_dip':
                    explanation = f"{base_str} {direction_verb} by {abs(pct_change):.0f}% at {time_str} due to {driver_str}."
                    direction_flag = "decrease"

                insights.append({
                    "time": time_str,
                    "explanation": explanation,
                    "impact_percent": float(primary_impact_percent),
                    "direction": direction_flag,
                    "type": item['type']
                })
                
            # Compute a synthetic confidence score based on the variance of SHAP values
            # (Less variance across all predictions = more stable/confident model)
            shap_variance = np.var(load_shap_values)
            confidence_score = max(0.6, min(0.98, 1.0 - (shap_variance / 10000)))

            return {
                "insights": insights,
                "confidence_score": float(confidence_score)
            }
            
        except Exception as e:
            print(f"SHAP explanation failed: {str(e)}")
            return {"insights": [], "confidence_score": 0.5, "error": str(e)}

    def explain_decision(self, results, config):
        # Legacy optimizer insights
        pass

    def explain_dispatch(self, schedule, load_forecast, solar_forecast, tariff_profile):
        """
        Generates business logic explanations for the mathematical dispatch schedule.
        Identifies why the real-time engine chose to charge/discharge at specific times.
        """
        explanations = []
        
        # Find peak discharge event
        discharges = [s for s in schedule if s['action'] == 'DISCHARGE']
        if discharges:
            peak_dis = max(discharges, key=lambda x: x['power'])
            t_idx = int(peak_dis['time'].split(':')[0]) * 4 + int(peak_dis['time'].split(':')[1]) // 15
            tariff = tariff_profile[t_idx]
            load = load_forecast[t_idx]
            explanations.append({
                "time": peak_dis['time'] + " PM" if int(peak_dis['time'].split(':')[0]) >= 12 else peak_dis['time'] + " AM",
                "explanation": f"Discharging {peak_dis['power']:.1f} kW to offset high site load ({load:.1f} kW) during peak tariff period (₹{tariff:.2f}/kWh).",
                "impact_percent": 60.0,
                "direction": "decrease",
                "type": "peak_shaving"
            })
            
        # Find peak charge event
        charges = [s for s in schedule if s['action'] == 'CHARGE']
        if charges:
            peak_char = max(charges, key=lambda x: x['power'])
            t_idx = int(peak_char['time'].split(':')[0]) * 4 + int(peak_char['time'].split(':')[1]) // 15
            tariff = tariff_profile[t_idx]
            solar = solar_forecast[t_idx]
            
            reason = "excess solar generation" if solar > 10 else f"low off-peak tariff (₹{tariff:.2f}/kWh)"
            
            explanations.append({
                "time": peak_char['time'] + " PM" if int(peak_char['time'].split(':')[0]) >= 12 else peak_char['time'] + " AM",
                "explanation": f"Charging {peak_char['power']:.1f} kW due to {reason}.",
                "impact_percent": 40.0,
                "direction": "increase",
                "type": "arbitrage"
            })
            
        return explanations
