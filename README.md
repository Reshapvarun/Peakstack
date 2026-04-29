# Peakstack: AI-Powered BESS Investment Advisor

Peakstack is a SaaS platform designed to help industrial clients in India optimize Battery Energy Storage System (BESS) investments. It combines machine learning forecasts with a high-fidelity industrial billing engine.

## 🚀 Key Features
*   **HT Billing Engine:** Simulates realistic Indian industrial electricity bills including Time-of-Day (ToD) rates and demand charges.
*   **Automated Tariff Updates:** Monitors state regulator websites for changes in energy policies.
*   **Decision Intelligence:** Compares CAPEX, EaaS, and Hybrid business models to find the best ROI.
*   **XAI Integration:** Provides explainable AI insights into battery charging/discharging decisions.

## 📂 Core Structure
*   `main_2.py`: FastAPI entry point and orchestration layer.
*   `engine.py`: Logic for calculating energy, demand, and fixed charges.
*   `decision_engine.py`: Multi-factor scoring for optimal battery sizing.
*   `data_ingestion.py`: Pre-processing for demo and real-world CSV data.

## 🛠️ Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Ensure `config/state_tariffs.json` is populated with valid state data.
3. Run the server: `python app/api/main_2.py`