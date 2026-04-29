import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import logo from "./assets/logo.png";

import {
  BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid,
  LineChart, Line, ResponsiveContainer
} from "recharts";

import html2canvas from "html2canvas";
import jsPDF from "jspdf";

export default function App() {
  const [data, setData] = useState(null);
  const [dark, setDark] = useState(false);

  useEffect(() => {
    document.body.className = dark ? "dark" : "";
  }, [dark]);

  const runAnalysis = async () => {
    try {
      const res = await axios.post("http://127.0.0.1:8000/analyze", {
        battery_kwh: 600,
        battery_kw: 200,
        solar_kw: 400,
        wind_kw: 100
      });
      setData(res.data);
    } catch (err) {
      alert("Backend not running");
    }
  };

  const downloadPDF = async () => {
    const element = document.getElementById("report");
    const canvas = await html2canvas(element);
    const imgData = canvas.toDataURL("image/png");

    const pdf = new jsPDF("landscape");
    pdf.addImage(imgData, "PNG", 10, 10, 280, 150);
    pdf.save("PeakStack_Report.pdf");
  };

  const barData = [
    { name: "Without BESS", cost: data?.without_bess || 498000 },
    { name: "With BESS", cost: data?.with_bess || 336000 }
  ];

  const lineData = data?.load_profile || [
    { time: "00", load: 200 },
    { time: "06", load: 350 },
    { time: "12", load: 550 },
    { time: "18", load: 450 },
    { time: "24", load: 300 }
  ];

  return (
    <div className="layout" id="report">

      {/* SIDEBAR */}
      <div className="sidebar">
        <img src={logo} className="logo" alt="logo" />

        <h3>CONFIGURATION</h3>

        <button className="run-btn" onClick={runAnalysis}>
          🚀 Run Investment Analysis
        </button>

        <button className="toggle" onClick={() => setDark(!dark)}>
          {dark ? "☀️ Light Mode" : "🌙 Dark Mode"}
        </button>
      </div>

      {/* MAIN */}
      <div className="main">

        {/* HEADER */}
        <div className="top-bar">
          <div>
            <h1>PEAKSTACK ENERGY</h1>
            <p className="subtitle">Smart Energy Investment Platform</p>
          </div>

          <button className="download" onClick={downloadPDF}>
            📄 Download Report
          </button>
        </div>

        {/* SUMMARY */}
        {data && (
          <div className="summary">
            ✅ This facility can save ₹{data.monthly_savings.toLocaleString()}/month
            with a {data.battery_kwh} kWh BESS system
          </div>
        )}

        {/* RECOMMEND */}
        {data && (
          <div className="recommend">
            <h2>🏆 INSTALL BESS</h2>
            <p>AI strongly recommends installing a BESS system</p>

            <div className="rec-grid">
              <div>
                <span>Recommended Size</span>
                <h3>{data.battery_kwh} kWh</h3>
              </div>

              <div>
                <span>Payback</span>
                <h3>{data.payback_years} Years</h3>
              </div>

              <div>
                <span>Confidence</span>
                <span className="badge">HIGH</span>
              </div>
            </div>
          </div>
        )}

        {/* KPI CARDS */}
        {data && (
          <div className="cards">
            <div className="card">
              <h4>Monthly Savings</h4>
              <h2>₹{data.monthly_savings.toLocaleString()}</h2>
            </div>

            <div className="card">
              <h4>Payback</h4>
              <h2>{data.payback_years} yrs</h2>
            </div>

            <div className="card">
              <h4>Peak Reduction</h4>
              <h2>{data.peak_reduction}%</h2>
            </div>
          </div>
        )}

        {/* CHARTS */}
        {data && (
          <div className="charts">

            <div className="chart-box">
              <h3>Cost Comparison</h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={barData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="cost" fill="#22c55e" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-box">
              <h3>Load Profile</h3>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={lineData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="load" stroke="#2563eb" />
                </LineChart>
              </ResponsiveContainer>
            </div>

          </div>
        )}

        {/* INSIGHTS */}
        {data && (
          <div className="insights">
            <h3>Key Insights</h3>
            <ul>
              <li>✔ Peak shaving reduces evening demand charges</li>
              <li>✔ Optimized energy sourcing reduces cost</li>
              <li>✔ BESS improves reliability</li>
            </ul>
          </div>
        )}

      </div>
    </div>
  );
}