# 🚀 Quick Start Checklist

## Backend Setup

- [ ] Install Python 3.9+
- [ ] Create virtual environment: `python -m venv venv`
- [ ] Activate: `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
- [ ] Install deps: `pip install -r requirements.txt`
- [ ] Verify FastAPI installed: `pip show fastapi`
- [ ] Start server: `uvicorn app.api.main:app --reload --port 8000`
- [ ] Check health: `curl http://localhost:8000/health`
- [ ] View API docs: Open `http://localhost:8000/docs`

## Frontend Setup

- [ ] Node.js 16+ installed
- [ ] Navigate to `peakstack-ui/`: `cd peakstack-ui`
- [ ] Install dependencies: `npm install`
- [ ] Set API URL (optional): `export REACT_APP_API_URL=http://localhost:8000/api/v1`
- [ ] Start dev server: `npm start`
- [ ] Browser opens to `http://localhost:3000`

## First Analysis

- [ ] Fill form (State: Maharashtra, Battery: 250 kWh, Solar: 100 kW)
- [ ] Click "🚀 Run Analysis"
- [ ] ⏳ Wait for 6-stage pipeline (~5-10 seconds)
- [ ] ✅ See KPIs, charts, insights, realism gap
- [ ] 📄 Click "Download PDF" to save report

## Verify Everything Works

### Backend

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "state": "maharashtra",
    "battery_kwh": 250,
    "battery_power_kw": 75,
    "solar_kw": 100,
    "annual_kwh": 500000
  }'
```

Expected response: `AnalysisResponse` JSON with all fields

### Frontend

- Form validation works (try invalid values)
- API call succeeds
- Charts render
- Insights display
- Realism gap shows "Theoretical → Realistic" conversion

## File Locations

```
Backend:
✅ app/pipeline.py              (PipelineOrchestrator)
✅ app/schemas.py               (Pydantic models)
✅ app/api/routes.py            (FastAPI /analyze endpoint)

Frontend:
✅ peakstack-ui/src/services/api.js           (API client)
✅ peakstack-ui/src/App_production.jsx        (Main app)
✅ peakstack-ui/src/components/Charts.jsx     (Dynamic charts)
✅ peakstack-ui/src/components/Insights.jsx   (Dynamic insights)
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: app` | Run from project root, not subdirectory |
| CORS error | Backend CORS middleware already configured |
| API not found | Backend running on 8000? Frontend points to correct URL? |
| Charts not showing | Check browser console for errors |
| Form validation fails | See error message in red alert |

## Next Steps

1. **Test with real data:** Upload CSV with actual load profile
2. **Customize tariffs:** Update state-specific rates in `app/core/`
3. **Tune financial assumptions:** Modify CAPEX/O&M in pipeline
4. **Refactor architecture:** Follow TASK #9 guide (domain/application/infra layers)
5. **Deploy:** Docker + FastAPI on cloud (AWS/GCP/Azure)

---

**Time estimate: 30-60 minutes from zero to working system**
