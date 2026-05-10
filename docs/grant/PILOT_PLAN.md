This pilot plan is submitted as part of the DPIIT SISFS 
proof-of-concept grant application for ₹20 Lakhs.

# Pilot Deployment Plan

**Target Site Profile:**
*   **Sector:** Textile Mill or Pharmaceutical Manufacturing (predictable load patterns).
*   **State:** Tamil Nadu (High TANGEDCO HT-1 demand charges).
*   **Connected Load:** 300-500 kVA.
*   **BESS Requirement:** 250-500 kWh LFP System.
*   **Monthly Bill:** ₹8–₹15 Lakhs.

**Operational Workflow:**
1.  **Connectivity:** Establish secure Modbus/RS485 or Cloud API connection to the BESS inverter.
2.  **Telemetry:** Real-time data acquisition of site load and battery status every 15 minutes.
3.  **Dispatch:** Autonomous command execution based on the TANGEDCO ToD peak-shaving schedule.
4.  **Monitoring:** Continuous data logging to the Peakstack cloud dashboard for performance tracking.

**Success Metrics:**
*   **Primary:** ≥15% reduction in monthly fixed demand charges (kVA).
*   **Secondary:** ≥10% reduction in the total monthly electricity bill.
*   **Reliability:** BESS State-of-Charge (SOC) maintained strictly within the 20-90% health window.
*   **Reporting:** Delivery of a verified "Actual vs. Baseline" savings report.

**Timeline:** 90 Days from disbursement to data validation.
**Budget:** ₹6 Lakhs.
**Risk Mitigation:** Implementation of a 30-day "Shadow Mode" phase to validate dispatch logic against real load profiles before live battery control.
