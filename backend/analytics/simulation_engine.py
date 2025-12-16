"""
Estate Planning Simulation Engine

Handles scenario modeling and what-if analysis for estate plans:
- Monte Carlo simulations for uncertainty
- Sensitivity analysis
- Variable modification scenarios
- Outcome comparison
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable
from decimal import Decimal
from enum import Enum
import random
import math

from .calculations.federal_estate_tax import FederalEstateTaxCalculator
from .calculations.state_estate_tax import StateEstateTaxCalculator, calculate_state_tax_apportionment
from .calculations.gst_calculations import GSTExemptionTracker


class VariableType(Enum):
    """Types of variables that can be modified in scenarios"""
    ASSET_VALUE = "asset_value"
    GROWTH_RATE = "growth_rate"
    LIFE_EXPECTANCY = "life_expectancy"
    TAX_RATE = "tax_rate"
    INFLATION_RATE = "inflation_rate"
    GIFTING_STRATEGY = "gifting_strategy"
    SURVIVAL_RATE = "survival_rate"


@dataclass
class ScenarioVariable:
    """Variable to modify in a scenario"""
    name: str
    variable_type: VariableType
    base_value: Decimal
    scenario_value: Decimal
    description: str = ""


@dataclass
class SimulationResult:
    """Results from a single simulation run"""
    scenario_name: str
    total_estate_value: Decimal
    federal_estate_tax: Decimal
    state_estate_tax: Decimal
    total_taxes: Decimal
    net_to_heirs: Decimal
    net_to_spouse: Decimal
    net_to_children: Decimal
    net_to_charity: Decimal
    distribution_by_beneficiary: Dict[str, Decimal] = field(default_factory=dict)
    gst_tax: Decimal = Decimal(0)
    assumptions_used: Dict = field(default_factory=dict)


@dataclass
class MonteCarloResult:
    """Statistical results from Monte Carlo simulation"""
    scenario_name: str
    iterations: int
    average_net_to_heirs: Decimal
    median_net_to_heirs: Decimal
    min_net_to_heirs: Decimal
    max_net_to_heirs: Decimal
    std_deviation: Decimal
    percentile_10: Decimal
    percentile_25: Decimal
    percentile_75: Decimal
    percentile_90: Decimal
    probability_of_estate_tax: Decimal
    average_estate_tax: Decimal


class EstateSimulationEngine:
    """
    Run estate planning simulations with variable scenarios.
    """

    def __init__(self, year: int = 2024):
        self.year = year
        self.federal_calculator = FederalEstateTaxCalculator(year)
        self.state_calculator = StateEstateTaxCalculator(year)
        self.gst_tracker = GSTExemptionTracker(year)

    def run_scenario(
        self,
        scenario_name: str,
        base_estate: Dict,  # {asset descriptions: values}
        variables: List[ScenarioVariable],
        domicile_state: str = "NY",
        marital_deduction: Decimal = Decimal(0),
        charitable_deduction: Decimal = Decimal(0),
    ) -> SimulationResult:
        """
        Run a single estate planning scenario.

        Args:
            scenario_name: Name of the scenario
            base_estate: Base estate asset values
            variables: Variables to modify for this scenario
            domicile_state: State where person is domiciled
            marital_deduction: Amount passing to spouse
            charitable_deduction: Amount to charity

        Returns:
            Simulation results for the scenario
        """

        # Apply scenario variables to estate
        modified_estate = self._apply_variables(base_estate, variables)

        # Calculate total estate value after modifications
        total_estate_value = sum(Decimal(str(v)) for v in modified_estate.values())

        # Calculate federal estate tax
        federal_tax_calc = self.federal_calculator.calculate_federal_estate_tax(
            gross_estate=total_estate_value,
            marital_deduction=marital_deduction,
            charitable_deduction=charitable_deduction,
        )

        # Calculate state estate tax
        state_tax_calc = self.state_calculator.calculate_state_estate_tax(
            state=domicile_state,
            taxable_estate=federal_tax_calc["taxable_estate"],
            domicile_state=domicile_state,
        )

        # Total taxes
        total_taxes = (
            federal_tax_calc["federal_estate_tax"]
            + state_tax_calc["state_estate_tax"]
        )

        # Calculate distributions
        net_total = total_estate_value - total_taxes
        net_to_spouse = marital_deduction
        net_to_charity = charitable_deduction
        net_to_heirs = net_total - net_to_spouse - net_to_charity

        return SimulationResult(
            scenario_name=scenario_name,
            total_estate_value=total_estate_value,
            federal_estate_tax=federal_tax_calc["federal_estate_tax"],
            state_estate_tax=state_tax_calc["state_estate_tax"],
            total_taxes=total_taxes,
            net_to_heirs=net_to_heirs,
            net_to_spouse=net_to_spouse,
            net_to_children=net_to_heirs,  # Simplified
            net_to_charity=net_to_charity,
            gst_tax=Decimal(0),  # Would calculate if transfers to skip persons
            assumptions_used={
                "year": self.year,
                "domicile_state": domicile_state,
                "variables_applied": {v.name: str(v.scenario_value) for v in variables},
            },
        )

    def run_monte_carlo_simulation(
        self,
        scenario_name: str,
        base_estate: Dict,
        variable_distributions: Dict[str, Tuple[Decimal, Decimal]],  # {var_name: (mean, std_dev)}
        iterations: int = 1000,
        domicile_state: str = "NY",
        marital_deduction: Decimal = Decimal(0),
        charitable_deduction: Decimal = Decimal(0),
    ) -> MonteCarloResult:
        """
        Run Monte Carlo simulation with probabilistic variables.

        Args:
            scenario_name: Name of scenario
            base_estate: Base estate values
            variable_distributions: Variables and their normal distributions
            iterations: Number of Monte Carlo iterations
            domicile_state: State of domicile
            marital_deduction: Amount to spouse
            charitable_deduction: Amount to charity

        Returns:
            Statistical results from Monte Carlo
        """

        results = []
        tax_occurring = 0

        for _ in range(iterations):
            # Generate random variables from distributions
            variables = self._generate_random_variables(variable_distributions)

            # Run scenario
            result = self.run_scenario(
                scenario_name=f"{scenario_name} (MC iteration)",
                base_estate=base_estate,
                variables=variables,
                domicile_state=domicile_state,
                marital_deduction=marital_deduction,
                charitable_deduction=charitable_deduction,
            )

            results.append(result)

            # Track if estate tax occurred
            if result.federal_estate_tax > 0:
                tax_occurring += 1

        # Calculate statistics
        net_to_heirs_values = [r.net_to_heirs for r in results]
        net_to_heirs_values.sort()

        return MonteCarloResult(
            scenario_name=scenario_name,
            iterations=iterations,
            average_net_to_heirs=Decimal(str(sum(net_to_heirs_values) / len(net_to_heirs_values))),
            median_net_to_heirs=net_to_heirs_values[len(net_to_heirs_values) // 2],
            min_net_to_heirs=min(net_to_heirs_values),
            max_net_to_heirs=max(net_to_heirs_values),
            std_deviation=self._calculate_std_dev(net_to_heirs_values),
            percentile_10=net_to_heirs_values[int(len(net_to_heirs_values) * 0.10)],
            percentile_25=net_to_heirs_values[int(len(net_to_heirs_values) * 0.25)],
            percentile_75=net_to_heirs_values[int(len(net_to_heirs_values) * 0.75)],
            percentile_90=net_to_heirs_values[int(len(net_to_heirs_values) * 0.90)],
            probability_of_estate_tax=Decimal(tax_occurring) / Decimal(iterations),
            average_estate_tax=Decimal(
                str(sum(r.total_taxes for r in results) / len(results))
            ),
        )

    def run_sensitivity_analysis(
        self,
        base_estate: Dict,
        test_variable: ScenarioVariable,
        value_range: Tuple[Decimal, Decimal],
        steps: int = 10,
        domicile_state: str = "NY",
        marital_deduction: Decimal = Decimal(0),
        charitable_deduction: Decimal = Decimal(0),
    ) -> List[Dict]:
        """
        Run sensitivity analysis on a single variable.

        Args:
            base_estate: Base estate values
            test_variable: Variable to test
            value_range: (min_value, max_value) to test
            steps: Number of steps in range
            domicile_state: State of domicile
            marital_deduction: Amount to spouse
            charitable_deduction: Amount to charity

        Returns:
            List of results at each step
        """

        results = []
        min_val, max_val = value_range
        step_size = (max_val - min_val) / Decimal(steps)

        for i in range(steps + 1):
            current_value = min_val + (step_size * i)

            # Create variable for this step
            variable = ScenarioVariable(
                name=test_variable.name,
                variable_type=test_variable.variable_type,
                base_value=test_variable.base_value,
                scenario_value=current_value,
                description=test_variable.description,
            )

            # Run scenario
            result = self.run_scenario(
                scenario_name=f"Sensitivity: {test_variable.name}={current_value}",
                base_estate=base_estate,
                variables=[variable],
                domicile_state=domicile_state,
                marital_deduction=marital_deduction,
                charitable_deduction=charitable_deduction,
            )

            results.append({
                "variable_value": current_value,
                "total_estate_value": result.total_estate_value,
                "federal_estate_tax": result.federal_estate_tax,
                "total_taxes": result.total_taxes,
                "net_to_heirs": result.net_to_heirs,
            })

        return results

    def compare_scenarios(
        self,
        base_estate: Dict,
        scenarios: List[Dict],  # [{name: str, variables: [...]}, ...]
        domicile_state: str = "NY",
        marital_deduction: Decimal = Decimal(0),
        charitable_deduction: Decimal = Decimal(0),
    ) -> Dict:
        """
        Compare multiple scenarios and rank them.

        Args:
            base_estate: Base estate
            scenarios: List of scenarios to compare
            domicile_state: State of domicile
            marital_deduction: Amount to spouse
            charitable_deduction: Amount to charity

        Returns:
            Comparison with rankings
        """

        results = []

        for scenario in scenarios:
            result = self.run_scenario(
                scenario_name=scenario.get("name", "Unnamed"),
                base_estate=base_estate,
                variables=scenario.get("variables", []),
                domicile_state=domicile_state,
                marital_deduction=marital_deduction,
                charitable_deduction=charitable_deduction,
            )

            results.append(result)

        # Rank by net to heirs (best outcome)
        ranked_results = sorted(results, key=lambda r: r.net_to_heirs, reverse=True)

        return {
            "scenarios_compared": len(results),
            "ranked_scenarios": [
                {
                    "rank": i + 1,
                    "scenario_name": r.scenario_name,
                    "total_estate_value": r.total_estate_value,
                    "total_taxes": r.total_taxes,
                    "net_to_heirs": r.net_to_heirs,
                    "tax_efficiency": (
                        (1 - r.total_taxes / r.total_estate_value) * 100
                        if r.total_estate_value > 0 else 0
                    ),
                }
                for i, r in enumerate(ranked_results)
            ],
            "best_scenario": ranked_results[0].scenario_name if ranked_results else None,
            "tax_savings_best_vs_worst": (
                ranked_results[0].net_to_heirs - ranked_results[-1].net_to_heirs
                if ranked_results else Decimal(0)
            ),
        }

    def calculate_strategy_impact(
        self,
        base_estate_value: Decimal,
        strategy_name: str,
        strategy_impact: Dict,
        # strategy_impact keys: {"tax_reduction": Decimal, "exemption_preserved": Decimal, ...}
    ) -> Dict:
        """
        Calculate impact of a specific estate planning strategy.

        Args:
            base_estate_value: Estate value before strategy
            strategy_name: Name of strategy
            strategy_impact: Dictionary with impact calculations

        Returns:
            Strategy impact analysis
        """

        # Example strategies:
        # ILIT, Spousal Lifetime Access Trust (SLAT), Qualified Charitable Remainder Trust (QCRT)
        # etc.

        federal_tax_savings = strategy_impact.get("tax_reduction", Decimal(0))
        exemption_preserved = strategy_impact.get("exemption_preserved", Decimal(0))
        wealth_transferred = strategy_impact.get("wealth_transferred", Decimal(0))

        return {
            "strategy": strategy_name,
            "base_estate_value": base_estate_value,
            "federal_estate_tax_savings": federal_tax_savings,
            "exemption_preserved": exemption_preserved,
            "wealth_transferred_tax_free": wealth_transferred,
            "effective_tax_savings_per_dollar": (
                federal_tax_savings / base_estate_value
                if base_estate_value > 0 else Decimal(0)
            ),
            "ranking": self._rank_strategy_effectiveness(federal_tax_savings),
        }

    def project_estate_growth(
        self,
        current_estate_value: Decimal,
        annual_growth_rate: Decimal,
        years: int,
        annual_additions: Decimal = Decimal(0),
    ) -> List[Dict]:
        """
        Project estate growth over time.

        Args:
            current_estate_value: Current estate value
            annual_growth_rate: Expected annual growth rate
            years: Number of years to project
            annual_additions: Annual contributions/additions

        Returns:
            Year-by-year projection
        """

        projections = []
        current_value = current_estate_value

        for year in range(1, years + 1):
            current_value = current_value * (1 + annual_growth_rate) + annual_additions

            # Estimate estate tax at this value
            estate_tax_estimate = self.federal_calculator.calculate_federal_estate_tax(
                gross_estate=current_value
            )

            projections.append({
                "year": year,
                "projected_estate_value": current_value,
                "estimated_federal_estate_tax": estate_tax_estimate["federal_estate_tax"],
                "estimated_net_to_heirs": estate_tax_estimate["net_to_heirs"],
            })

        return projections

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    @staticmethod
    def _apply_variables(
        base_estate: Dict,
        variables: List[ScenarioVariable],
    ) -> Dict:
        """Apply scenario variables to base estate"""

        modified_estate = base_estate.copy()

        for variable in variables:
            if variable.variable_type == VariableType.ASSET_VALUE:
                # Modify specific asset value
                if variable.name in modified_estate:
                    modified_estate[variable.name] = variable.scenario_value

            elif variable.variable_type == VariableType.GROWTH_RATE:
                # Apply growth rate to all assets
                multiplier = 1 + variable.scenario_value
                for key in modified_estate:
                    modified_estate[key] = Decimal(str(modified_estate[key])) * Decimal(str(multiplier))

        return modified_estate

    @staticmethod
    def _generate_random_variables(
        variable_distributions: Dict[str, Tuple[Decimal, Decimal]],
    ) -> List[ScenarioVariable]:
        """Generate random variables from normal distributions"""

        variables = []

        for var_name, (mean, std_dev) in variable_distributions.items():
            # Generate from normal distribution
            random_value = Decimal(str(
                random.gauss(float(mean), float(std_dev))
            ))

            # Ensure non-negative
            random_value = max(Decimal(0), random_value)

            variables.append(
                ScenarioVariable(
                    name=var_name,
                    variable_type=VariableType.ASSET_VALUE,
                    base_value=mean,
                    scenario_value=random_value,
                )
            )

        return variables

    @staticmethod
    def _calculate_std_dev(values: List[Decimal]) -> Decimal:
        """Calculate standard deviation"""
        if len(values) < 2:
            return Decimal(0)

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = math.sqrt(float(variance))

        return Decimal(str(std_dev))

    @staticmethod
    def _rank_strategy_effectiveness(tax_savings: Decimal) -> str:
        """Rank strategy effectiveness"""
        if tax_savings > Decimal("500000"):
            return "Excellent"
        elif tax_savings > Decimal("250000"):
            return "Very Good"
        elif tax_savings > Decimal("100000"):
            return "Good"
        else:
            return "Moderate"
