import json
import os
from typing import Dict, Any, Tuple, List
import numpy as np
import pandas as pd
from app.core.billing.models import HTTariffModel, StateConfiguration
from app.core.tariff import DEFAULT_TARIFF # Keep for backward compatibility if needed

class TariffEngine:
    """
    Production-grade Industrial HT Billing Engine.
    Calculates monthly electricity bills based on realistic Indian HT tariff structures,
    including Time-of-Day (ToD) pricing, demand charges, and Power Factor penalties.
    """
    def __init__(self, state: str, config_path: str = "config/state_tariffs.json"):
        self.state = state
        self.config_path = config_path
        self.tariff = self._load_tariff()

    def _load_tariff(self) -> HTTariffModel:
        with open(self.config_path, 'r') as f:
            data = json.load(f)

        if self.state not in data:
            raise ValueError(f"Tariff data not found for state: {self.state}")

        return HTTariffModel(**data[self.state])

    def get_rate_for_hour(self, hour: int) -> float:
        """Returns the energy rate based on ToD window."""
        if hour in self.tariff.tod_hours.peak:
            return self.tariff.energy_rate.peak
        elif hour in self.tariff.tod_hours.off_peak:
            return self.tariff.energy_rate.off_peak
        else:
            return self.tariff.energy_rate.normal

    def calculate_energy_cost(self, energy_kwh: float, hour: int) -> float:
        """Calculates cost for a specific energy block."""
        return energy_kwh * self.get_rate_for_hour(hour)

    def calculate_demand_charge(self, actual_peak_kva: float, sanctioned_demand_kva: float) -> float:
        """
        Calculates demand charges with penalty for exceeding sanctioned limit.
        Rule: If actual > sanctioned, penalty multiplier applies.
        """
        chargeable_demand = max(actual_peak_kva, sanctioned_demand_kva)
        base_cost = chargeable_demand * self.tariff.demand_charge_per_kva

        penalty = 0.0
        if actual_peak_kva > sanctioned_demand_kva:
            # Typical HT penalty: 1.5x or 2x the demand charge for the excess
            excess = actual_peak_kva - sanctioned_demand_kva
            penalty = excess * self.tariff.demand_charge_per_kva * 1.5

        return base_cost + penalty

    def calculate_fixed_charge(self, sanctioned_demand_kva: float) -> float:
        """Flat monthly fixed charge based on contract demand."""
        return sanctioned_demand_kva * self.tariff.fixed_charge_per_kva

    def calculate_pf_impact(self, current_pf: float) -> float:
        """
        Calculates Power Factor penalty or incentive.
        Rule: PF < threshold -> Penalty; PF > incentive_threshold -> Incentive.
        """
        if current_pf < self.tariff.pf_penalty_threshold:
            # Penalty is often a % of the total bill or a flat rate per kVA
            # For this model, we use a simplified % penalty of the energy cost
            return 0.05 * (1.0 / (current_pf + 1e-6)) * 100 # Simplified penalty
        elif current_pf > self.tariff.pf_incentive_threshold:
            # Incentive as a reduction in demand charges
            return -0.02 * 100 # Simplified incentive
        return 0.0

    def calculate_monthly_bill(self, load_profile: pd.DataFrame, sanctioned_demand_kva: float, pf: float = 0.95) -> Dict[str, Any]:
        """
        Full monthly billing simulation.
        Args:
            load_profile: DataFrame with columns ['timestamp', 'net_load_kw']
            sanctioned_demand_kva: The contract demand
            pf: Average power factor
        """
        # 1. Energy Charges (ToD)
        total_energy_cost = 0.0
        for _, row in load_profile.iterrows():
            hour = row['timestamp'].hour
            energy_kwh = row['net_load_kw'] * 0.25 # 15-min interval
            total_energy_cost += self.calculate_energy_cost(energy_kwh, hour)

        # 2. Demand Charges
        actual_peak = load_profile['net_load_kw'].max()
        demand_cost = self.calculate_demand_charge(actual_peak, sanctioned_demand_kva)

        # 3. Fixed Charges
        fixed_cost = self.calculate_fixed_charge(sanctioned_demand_kva)

        # 4. PF Impact
        pf_cost = self.calculate_pf_impact(pf)

        # 5. Subtotal & Taxes
        subtotal = total_energy_cost + demand_cost + fixed_cost + pf_cost
        tax = subtotal * (self.tariff.tax_percent / 100.0)
        total_bill = subtotal + tax

        return {
            "energy_cost": total_energy_cost,
            "demand_cost": demand_cost,
            "fixed_cost": fixed_cost,
            "pf_impact": pf_cost,
            "tax": tax,
            "total_bill": total_bill,
            "actual_peak": actual_peak,
            "sanctioned_demand": sanctioned_demand_kva
        }
