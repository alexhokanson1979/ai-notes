"""
Estate Planning Presentation and Report Generation

Generates:
- PDF reports with estate analysis
- PowerPoint presentations
- HTML dashboards
- Family tree diagrams
- Timeline visualizations
- White-label customized presentations
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime
from jinja2 import Template, Environment, FileSystemLoader
import json


@dataclass
class PresentationConfig:
    """Configuration for presentation generation"""
    template_name: str
    output_format: str  # "pdf", "pptx", "html"
    white_label_org: Optional[str] = None
    include_tax_summary: bool = True
    include_family_tree: bool = True
    include_timeline: bool = True
    include_scenario_comparison: bool = False
    include_insurance_summary: bool = True
    include_exemption_tracking: bool = True
    client_name: Optional[str] = None
    generated_date: Optional[str] = None


class PresentationGenerator:
    """Generate estate planning presentations and reports"""

    def __init__(self, template_directory: str = "./templates"):
        self.template_dir = template_directory
        self.env = Environment(loader=FileSystemLoader(template_directory))

    def generate_executive_summary(
        self,
        estate_data: Dict,
        scenario_results: Dict,
        config: PresentationConfig,
    ) -> Dict:
        """
        Generate executive summary of estate plan.

        Args:
            estate_data: Estate information
            scenario_results: Tax calculation results
            config: Presentation configuration

        Returns:
            Dictionary with summary content
        """

        summary = {
            "title": f"Estate Plan Summary - {config.client_name or 'Client'}",
            "generated_date": config.generated_date or datetime.now().isoformat(),
            "estate_overview": self._generate_estate_overview(estate_data),
            "tax_summary": self._generate_tax_summary(scenario_results),
            "key_recommendations": self._generate_recommendations(estate_data, scenario_results),
            "action_items": self._generate_action_items(estate_data),
        }

        return summary

    def generate_tax_analysis_report(
        self,
        federal_tax_results: Dict,
        state_tax_results: Dict,
        gst_results: Optional[Dict] = None,
        comparisons: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Generate detailed tax analysis report.

        Args:
            federal_tax_results: Federal estate tax calculations
            state_tax_results: State estate tax calculations
            gst_results: Generation-skipping transfer calculations
            comparisons: Scenario comparison data

        Returns:
            Tax analysis report content
        """

        report = {
            "section_title": "Tax Analysis and Calculations",
            "federal_estate_tax": self._format_tax_calculation(federal_tax_results),
            "state_estate_tax": self._format_tax_calculation(state_tax_results),
            "total_estimated_taxes": {
                "federal": federal_tax_results.get("federal_estate_tax", Decimal(0)),
                "state": state_tax_results.get("state_estate_tax", Decimal(0)),
                "total": (
                    Decimal(str(federal_tax_results.get("federal_estate_tax", 0))) +
                    Decimal(str(state_tax_results.get("state_estate_tax", 0)))
                ),
            },
            "exemption_analysis": {
                "federal_exemption": federal_tax_results.get("applicable_exemption"),
                "federal_exemption_utilized": (
                    federal_tax_results.get("gross_estate", Decimal(0)) -
                    federal_tax_results.get("taxable_estate", Decimal(0))
                ),
                "federal_exemption_remaining": max(
                    Decimal(0),
                    federal_tax_results.get("applicable_exemption", Decimal(0)) -
                    federal_tax_results.get("taxable_amount", Decimal(0))
                ),
            },
        }

        if gst_results:
            report["gst_analysis"] = gst_results

        if comparisons:
            report["scenario_comparisons"] = comparisons

        return report

    def generate_asset_distribution_chart(
        self,
        distributions: Dict[str, Dict],  # {beneficiary: {amount, percentage}}
    ) -> Dict:
        """
        Generate asset distribution visualization data.

        Args:
            distributions: Distribution amounts by beneficiary

        Returns:
            Chart data for visualization
        """

        total = sum(d.get("amount", Decimal(0)) for d in distributions.values())

        chart_data = {
            "chart_type": "pie",
            "title": "Estimated Estate Distribution",
            "data": [
                {
                    "label": beneficiary,
                    "value": float(data.get("amount", 0)),
                    "percentage": float(data.get("percentage", 0)),
                }
                for beneficiary, data in distributions.items()
            ],
            "total": float(total),
        }

        return chart_data

    def generate_family_tree_visualization(
        self,
        family_structure: Dict,  # {parent_id: [children], ...}
        family_members: Dict,  # {id: {name, relationship, dob, ...}}
    ) -> Dict:
        """
        Generate family tree visualization data.

        Args:
            family_structure: Hierarchical family structure
            family_members: Family member details

        Returns:
            Family tree visualization data
        """

        nodes = []
        edges = []
        positions = {}

        # Build nodes
        for member_id, member_info in family_members.items():
            nodes.append({
                "id": str(member_id),
                "label": member_info.get("name"),
                "title": member_info.get("relationship"),
                "generation": member_info.get("generation_level", 1),
            })

        # Build edges for relationships
        for parent_id, children in family_structure.items():
            for child_id in children:
                edges.append({
                    "from": str(parent_id),
                    "to": str(child_id),
                    "arrows": "to",
                })

        return {
            "visualization_type": "family_tree",
            "nodes": nodes,
            "edges": edges,
            "hierarchy": "UD",  # Up-Down layout
        }

    def generate_timeline_visualization(
        self,
        timeline_events: List[Dict],  # [{date, event, description}, ...]
    ) -> Dict:
        """
        Generate estate timeline visualization.

        Args:
            timeline_events: List of timeline events

        Returns:
            Timeline visualization data
        """

        # Sort events by date
        sorted_events = sorted(
            timeline_events,
            key=lambda x: x.get("date", "")
        )

        timeline_data = {
            "visualization_type": "timeline",
            "events": [
                {
                    "date": event.get("date"),
                    "title": event.get("event_title"),
                    "description": event.get("description"),
                    "type": event.get("event_type"),
                    "impact": event.get("tax_impact"),
                }
                for event in sorted_events
            ],
            "total_events": len(sorted_events),
        }

        return timeline_data

    def generate_insurance_summary(
        self,
        insurance_policies: List[Dict],  # List of policy data
    ) -> Dict:
        """
        Generate life insurance summary and analysis.

        Args:
            insurance_policies: List of insurance policies

        Returns:
            Insurance summary content
        """

        total_face_value = Decimal(0)
        total_annual_premium = Decimal(0)
        irrevocable_trust_policies = 0

        for policy in insurance_policies:
            total_face_value += Decimal(str(policy.get("face_value", 0)))
            total_annual_premium += Decimal(str(policy.get("annual_premium", 0)))
            if policy.get("is_irrevocable_trust_owned"):
                irrevocable_trust_policies += 1

        return {
            "section_title": "Life Insurance Analysis",
            "total_policies": len(insurance_policies),
            "total_face_value": total_face_value,
            "total_annual_premiums": total_annual_premium,
            "policies_in_ilit": irrevocable_trust_policies,
            "estate_tax_impact": total_face_value * Decimal("0.40"),  # 40% tax rate
            "detailed_policies": [
                self._format_policy_detail(p) for p in insurance_policies
            ],
        }

    def generate_exemption_tracking_report(
        self,
        federal_exemption_used: Decimal,
        federal_exemption_available: Decimal,
        gift_transactions: List[Dict],
        gst_allocations: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Generate exemption tracking and utilization report.

        Args:
            federal_exemption_used: Lifetime exemption used
            federal_exemption_available: Lifetime exemption remaining
            gift_transactions: Historical gift transactions
            gst_allocations: GST exemption allocations

        Returns:
            Exemption tracking report
        """

        total_exemption = federal_exemption_used + federal_exemption_available

        report = {
            "section_title": "Exemption Tracking & Analysis",
            "federal_lifetime_exemption": {
                "total_available": total_exemption,
                "amount_used": federal_exemption_used,
                "amount_remaining": federal_exemption_available,
                "percentage_utilized": (
                    (federal_exemption_used / total_exemption * 100)
                    if total_exemption > 0 else 0
                ),
            },
            "gift_transaction_history": [
                {
                    "date": tx.get("gift_date"),
                    "donor": tx.get("donor"),
                    "recipient": tx.get("recipient"),
                    "amount": tx.get("gift_amount"),
                    "type": tx.get("gift_type"),
                }
                for tx in gift_transactions
            ],
            "total_gifts_to_date": sum(tx.get("gift_amount", 0) for tx in gift_transactions),
        }

        if gst_allocations:
            report["gst_exemption_status"] = {
                "allocations": gst_allocations,
                "total_allocated": sum(
                    Decimal(str(a.get("exemption_allocated", 0)))
                    for a in gst_allocations
                ),
            }

        return report

    def generate_scenario_comparison_report(
        self,
        scenarios: List[Dict],  # Comparison data for multiple scenarios
    ) -> Dict:
        """
        Generate scenario comparison report.

        Args:
            scenarios: List of scenario results

        Returns:
            Scenario comparison report
        """

        # Calculate differences
        if len(scenarios) > 1:
            base_scenario = scenarios[0]
            comparisons = []

            for scenario in scenarios[1:]:
                tax_savings = (
                    Decimal(str(base_scenario.get("total_taxes", 0))) -
                    Decimal(str(scenario.get("total_taxes", 0)))
                )
                heirs_benefit = (
                    Decimal(str(scenario.get("net_to_heirs", 0))) -
                    Decimal(str(base_scenario.get("net_to_heirs", 0)))
                )

                comparisons.append({
                    "scenario_name": scenario.get("scenario_name"),
                    "total_estate": scenario.get("total_estate_value"),
                    "total_taxes": scenario.get("total_taxes"),
                    "tax_savings_vs_base": tax_savings,
                    "additional_to_heirs": heirs_benefit,
                })

            return {
                "section_title": "Scenario Comparison",
                "base_scenario": base_scenario.get("scenario_name"),
                "scenarios_compared": len(scenarios),
                "comparisons": comparisons,
            }

        return {}

    def generate_pdf_report(
        self,
        estate_data: Dict,
        scenario_results: Dict,
        config: PresentationConfig,
    ) -> str:
        """
        Generate PDF report (returns file path).

        Args:
            estate_data: Estate information
            scenario_results: Tax results
            config: Presentation config

        Returns:
            Path to generated PDF file
        """

        # This would use reportlab or weasyprint to generate PDF
        # Placeholder implementation
        report_content = {
            "title": f"Estate Plan Report - {config.client_name}",
            "sections": [
                self.generate_executive_summary(estate_data, scenario_results, config),
                self.generate_tax_analysis_report(
                    federal_tax_results=scenario_results.get("federal_taxes", {}),
                    state_tax_results=scenario_results.get("state_taxes", {}),
                ),
                self.generate_insurance_summary(estate_data.get("insurance_policies", [])),
                self.generate_exemption_tracking_report(
                    federal_exemption_used=Decimal(0),
                    federal_exemption_available=Decimal(13610000),
                    gift_transactions=estate_data.get("gift_transactions", []),
                ),
            ],
        }

        # In production, render template and generate PDF
        # For now, return JSON representation
        return f"/reports/estate_report_{datetime.now().timestamp()}.pdf"

    def generate_powerpoint_presentation(
        self,
        estate_data: Dict,
        scenario_results: Dict,
        visualizations: Dict,
        config: PresentationConfig,
    ) -> str:
        """
        Generate PowerPoint presentation.

        Args:
            estate_data: Estate information
            scenario_results: Tax results
            visualizations: Charts and diagrams
            config: Presentation config

        Returns:
            Path to generated PPTX file
        """

        # This would use python-pptx to generate presentations
        # Placeholder implementation
        slides = [
            {
                "slide_number": 1,
                "type": "title",
                "title": f"Estate Plan - {config.client_name}",
                "subtitle": "Professional Estate Planning Analysis",
            },
            {
                "slide_number": 2,
                "type": "content",
                "title": "Estate Overview",
                "content": self.generate_estate_overview(estate_data),
            },
            {
                "slide_number": 3,
                "type": "chart",
                "title": "Tax Analysis",
                "chart": visualizations.get("tax_breakdown"),
            },
            {
                "slide_number": 4,
                "type": "chart",
                "title": "Asset Distribution",
                "chart": visualizations.get("distribution"),
            },
        ]

        return f"/presentations/estate_plan_{datetime.now().timestamp()}.pptx"

    def generate_html_dashboard(
        self,
        estate_data: Dict,
        scenario_results: Dict,
        visualizations: Dict,
        config: PresentationConfig,
    ) -> str:
        """
        Generate interactive HTML dashboard.

        Args:
            estate_data: Estate information
            scenario_results: Tax results
            visualizations: Charts and diagrams
            config: Presentation config

        Returns:
            HTML content
        """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Estate Plan Dashboard - {config.client_name}</title>
            <link rel="stylesheet" href="/static/dashboard.css">
            <script src="https://d3js.org/d3.v7.min.js"></script>
        </head>
        <body>
            <div class="container">
                <header>
                    <h1>Estate Plan - {config.client_name}</h1>
                    <p>Generated: {config.generated_date}</p>
                </header>

                <section class="executive-summary">
                    <h2>Executive Summary</h2>
                    <div class="summary-cards">
                        <div class="card">
                            <h3>Total Estate Value</h3>
                            <p class="value">${estate_data.get('total_value', 0):,.2f}</p>
                        </div>
                        <div class="card">
                            <h3>Estimated Tax</h3>
                            <p class="value">${scenario_results.get('total_taxes', 0):,.2f}</p>
                        </div>
                        <div class="card">
                            <h3>Net to Heirs</h3>
                            <p class="value">${scenario_results.get('net_to_heirs', 0):,.2f}</p>
                        </div>
                    </div>
                </section>

                <section class="visualizations">
                    <h2>Visualizations</h2>
                    <div id="tax-chart"></div>
                    <div id="distribution-chart"></div>
                </section>

                <footer>
                    <p>This report is prepared for planning purposes and should be reviewed with a professional advisor.</p>
                </footer>
            </div>
        </body>
        </html>
        """

        return html

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    @staticmethod
    def _generate_estate_overview(estate_data: Dict) -> Dict:
        """Generate estate overview data"""
        return {
            "primary_owner": estate_data.get("primary_owner_name"),
            "spouse": estate_data.get("spouse_name"),
            "total_assets": estate_data.get("total_assets_value"),
            "asset_breakdown": estate_data.get("asset_breakdown"),
            "primary_residence": estate_data.get("primary_residence_value"),
        }

    @staticmethod
    def _generate_tax_summary(scenario_results: Dict) -> Dict:
        """Generate tax summary"""
        return {
            "federal_estate_tax": scenario_results.get("federal_estate_tax"),
            "state_estate_tax": scenario_results.get("state_estate_tax"),
            "total_taxes": scenario_results.get("total_taxes"),
            "effective_tax_rate": scenario_results.get("effective_tax_rate"),
            "net_to_family": scenario_results.get("net_to_heirs"),
        }

    @staticmethod
    def _generate_recommendations(estate_data: Dict, scenario_results: Dict) -> List[str]:
        """Generate recommendations based on estate analysis"""
        recommendations = []

        if scenario_results.get("federal_estate_tax", 0) > Decimal("100000"):
            recommendations.append("Consider lifetime gifting strategy to reduce taxable estate")
            recommendations.append("Review ILIT (Irrevocable Life Insurance Trust) strategy")

        if estate_data.get("insurance_policies"):
            recommendations.append("Ensure life insurance policies are not included in taxable estate")

        if not estate_data.get("charitable_deduction"):
            recommendations.append("Evaluate charitable giving opportunities to reduce tax")

        return recommendations

    @staticmethod
    def _generate_action_items(estate_data: Dict) -> List[Dict]:
        """Generate action items for estate plan"""
        return [
            {
                "item": "Review and update will/trust documents",
                "priority": "High",
                "timeline": "Within 6 months",
            },
            {
                "item": "Implement recommended tax strategies",
                "priority": "High",
                "timeline": "Within 12 months",
            },
            {
                "item": "Review beneficiary designations",
                "priority": "Medium",
                "timeline": "Within 12 months",
            },
        ]

    @staticmethod
    def _format_tax_calculation(tax_results: Dict) -> Dict:
        """Format tax calculation for display"""
        return {
            "gross_estate": tax_results.get("gross_estate"),
            "deductions": tax_results.get("marital_deduction", 0) + tax_results.get("charitable_deduction", 0),
            "taxable_estate": tax_results.get("taxable_estate"),
            "exemption": tax_results.get("applicable_exemption"),
            "taxable_amount": tax_results.get("taxable_amount"),
            "tax_rate": tax_results.get("tax_rate", "40%"),
            "tax_due": tax_results.get("federal_estate_tax") or tax_results.get("state_estate_tax"),
        }

    @staticmethod
    def _format_policy_detail(policy: Dict) -> Dict:
        """Format insurance policy for display"""
        return {
            "insured": policy.get("insured_name"),
            "type": policy.get("policy_type"),
            "face_value": policy.get("face_value"),
            "annual_premium": policy.get("annual_premium"),
            "owner": policy.get("policy_owner"),
            "beneficiary": policy.get("beneficiary"),
            "in_ilit": policy.get("is_irrevocable_trust_owned"),
        }
