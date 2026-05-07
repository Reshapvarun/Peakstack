# Peakstack EMS Platform

Peakstack is an Energy Management System (EMS) designed for industrial High Tension (HT) consumers in India. It optimizes Battery Energy Storage System (BESS) dispatch to reduce energy costs and peak demand charges.

## Features
- **Deterministic Dispatch Engine**: Rule-based battery control (Charge off-peak, Discharge peak).
- **Industrial Billing Engine**: Accurate calculation of energy and demand charges for Indian HT tariffs.
- **State-Specific Tariffs**: Pre-configured data for Tamil Nadu, Maharashtra, and Karnataka.
- **Analysis Pipeline**: Automated 6-stage pipeline for BESS investment assessment.

## Quick Start

### Prerequisites
- Python 3.8+
- Dependencies: `numpy`, `pandas` (optional, for advanced features)

### Running the Demo
To see the platform in action with a synthetic industrial load profile and real Tamil Nadu tariff data, run:

```bash
python run_demo.py
```

## Directory Structure
- `app/core/`: Core logic for dispatch and billing.
- `app/pipeline.py`: Pipeline orchestrator.
- `config/`: Configuration files (tariffs, etc.).
- `models/ml/`: Placeholder for future machine learning models.

## License
Proprietary