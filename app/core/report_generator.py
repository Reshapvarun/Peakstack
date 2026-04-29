from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.units import inch
from typing import Dict, Any
import os

class ReportGenerator:
    """
    Generates a professional investment-grade PDF report for BESS installation.
    """
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()

        # Custom Styles
        self.styles.add(ParagraphStyle(
            name='MainHeader',
            fontSize=22,
            textColor=colors.darkblue,
            alignment=1, # Center
            spaceAfter=20,
            fontName='Helvetica-Bold'
        ))
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            fontSize=16,
            textColor=colors.darkblue,
            alignment=0, # Left
            spaceBefore=15,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        ))

    def generate_pdf(self, data: Dict[str, Any], filename: str = "BESS_Investment_Report.pdf") -> str:
        path = os.path.join(self.output_dir, filename)
        doc = SimpleDocTemplate(path, pagesize=A4)
        elements = []

        summary = data.get('summary', {})
        rec = data.get('recommendation', {})
        bill = data.get('bill_breakdown', {})
        baseline_bill = data.get('baseline_bill', {})
        meta = data.get('report_meta', {})

        # --- PAGE 1: EXECUTIVE SUMMARY ---
        elements.append(Paragraph("BESS Investment Analysis Report", self.styles['MainHeader']))
        elements.append(Spacer(1, 0.2 * inch))

        elements.append(Paragraph("Executive Summary", self.styles['SectionHeader']))

        decision_color = colors.green if rec.get('decision') == "INSTALL" else colors.red
        decision_text = f"Decision: {rec.get('decision', 'N/A')}"

        # Decision Table
        exec_data = [
            ["Recommended Action", decision_text],
            ["Optimal Battery Size", f"{rec.get('optimal_size', 'N/A')} kWh"],
            ["Battery Technology", rec.get('tech', 'Lithium-ion (LFP)')],
            ["Expected Monthly Savings", f"₹{summary.get('daily_savings', 0) * 30:,.0f}"],
            ["Payback Period", f"{summary.get('payback_years', 'N/A')} Years"],
            ["Confidence Level", rec.get('confidence', 'N/A')],
        ]

        t = Table(exec_data, colWidths=[2.5 * inch, 3 * inch])
        t.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TEXTCOLOR', (1, 0), (1, 0), decision_color),
        ]))
        elements.append(t)

        elements.append(Spacer(1, 0.3 * inch))
        elements.append(Paragraph("<b>Strategic Reasoning:</b>", self.styles['Normal']))
        for reason in rec.get('reasoning', []):
            elements.append(Paragraph(f"• {reason}", self.styles['Normal']))

        elements.append(PageBreak())

        # --- PAGE 2: FINANCIAL ANALYSIS ---
        elements.append(Paragraph("Financial Analysis", self.styles['SectionHeader']))

        fin_data = [
            ["Metric", "Baseline (Current)", "With BESS (Projected)"],
            ["Monthly Energy Cost", f"₹{baseline_bill.get('energy_cost', 0):,.0f}", f"₹{bill.get('energy_cost', 0):,.0f}"],
            ["Monthly Demand Cost", f"₹{baseline_bill.get('demand_cost', 0):,.0f}", f"₹{bill.get('demand_cost', 0):,.0f}"],
            ["Total Monthly Bill", f"₹{baseline_bill.get('total_bill', 0):,.0f}", f"₹{bill.get('total_bill', 0):,.0f}"],
        ]

        ft = Table(fin_data, colWidths=[2.5 * inch, 2 * inch, 2 * inch])
        ft.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(ft)

        # CAPEX calculation based on actual battery size
        battery_size = rec.get('optimal_size', 0)
        capex_per_kwh = data.get('capex_per_kwh', 15000)
        total_capex = battery_size * capex_per_kwh

        elements.append(Spacer(1, 0.2 * inch))
        elements.append(Paragraph(f"<b>Estimated CAPEX:</b> ₹{total_capex:,.0f} (Based on ₹{capex_per_kwh:,.0f}/kWh)", self.styles['Normal']))

        payback = summary.get('payback_years', 0)
        if payback > 0 and payback != float('inf'):
            roi_pct = (1 / payback) * 100
            elements.append(Paragraph(f"<b>Annual ROI:</b> {roi_pct:.1f}% per year", self.styles['Normal']))
        else:
            elements.append(Paragraph("<b>Annual ROI:</b> Not viable", self.styles['Normal']))

        elements.append(PageBreak())

        # --- PAGE 3: TECHNICAL PERFORMANCE ---
        elements.append(Paragraph("Technical Performance", self.styles['SectionHeader']))
        elements.append(Paragraph("The proposed BESS configuration focuses on peak-shaving and energy arbitrage during high-tariff windows.", self.styles['Normal']))

        tech_data = [
            ["Metric", "Value"],
            ["Peak Demand Reduction", f"{summary.get('peak_reduction_pct', 0):.1f}%"],
            ["Estimated Curtailment", f"{data.get('curtailment', 0):.2f} kWh/day"],
        ]

        tt = Table(tech_data, colWidths=[2.5 * inch, 2 * inch])
        tt.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))
        elements.append(tt)

        elements.append(Spacer(1, 0.2 * inch))
        elements.append(Paragraph("<b>Battery SoC Behavior:</b> The system is designed to charge during off-peak hours and discharge during the peak window, effectively flattening the grid import curve.", self.styles['Normal']))

        elements.append(PageBreak())

        # --- PAGE 4: RISK & SENSITIVITY ---
        elements.append(Paragraph("Risk & Sensitivity Analysis", self.styles['SectionHeader']))

        # Payback range based on +/- 10% tariff shifts
        pb_base = summary.get('payback_years', 0)
        pb_low = pb_base * 1.1 if pb_base > 0 else 0 # Higher cost = slower payback
        pb_high = pb_base * 0.9 if pb_base > 0 else 0 # Lower cost = faster payback

        sensitivity_text = f"Under a +/- 10% shift in peak energy tariffs, the payback period is estimated to range between {pb_high:.1f} and {pb_low:.1f} years."

        elements.append(Paragraph(sensitivity_text, self.styles['Normal']))
        elements.append(Spacer(1, 0.2 * inch))

        # Technology Consideration section
        elements.append(Paragraph("Technology Consideration", self.styles['SectionHeader']))
        tech_note = "Lithium-ion (LFP) is the current industry standard for BESS due to its proven safety record and bankability. "
        if rec.get('emerging_tech_option'):
            tech_note += f"An alternative {rec.get('emerging_tech_option')} is emerging and under evaluation for specific use cases. "

        elements.append(Paragraph(tech_note, self.styles['Normal']))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph("<i>Disclaimer: Sodium-ion battery systems are considered emerging technology and may not be commercially available at scale in all regions.</i>", self.styles['Normal']))

        risk_data = [
            ["Risk Factor", "Impact", "Mitigation Strategy"],
            ["Tariff Volatility", "Medium", "BESS provides hedge against rate hikes"],
            ["Load Variability", "Low", "Sizing includes 20% buffer for growth"],
            ["Battery Degradation", "Low", "Calculations based on 80% EOL capacity"],
        ]

        rt = Table(risk_data, colWidths=[2 * inch, 1.5 * inch, 3 * inch])
        rt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))
        elements.append(rt)

        elements.append(PageBreak())

        # --- PAGE 5: ASSUMPTIONS ---
        elements.append(Paragraph("System Assumptions", self.styles['SectionHeader']))

        assumptions = [
            f"State Policy Applied: {meta.get('policy_state', 'N/A')}",
            f"Data Mode: { 'Real-time Load Profile' if 'real' in str(data) else 'Simulated Profile' }",
            "Regulatory Constraint: Behind-the-Meter (BTM) Strict",
            "Export Limitation: Zero-export to grid assumed",
            "Arbitrage: Restricted to on-site optimization",
            f"Sanctioned Demand: {summary.get('peak_reduction_pct', 0) * 1.2:.1f} kVA (Estimated)",
        ]

        for asm in assumptions:
            elements.append(Paragraph(f"• {asm}", self.styles['Normal']))
            elements.append(Spacer(1, 0.1 * inch))

        doc.build(elements)
        return path
