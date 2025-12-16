"""
State Estate and Inheritance Tax Calculation Engine

Only 12 states (plus DC) currently have estate taxes:
- Connecticut, Illinois, Maine, Maryland, Massachusetts,
  Minnesota, New York, Oregon, Rhode Island, Vermont,
  Washington, DC

Additionally, Iowa, Kentucky, Maryland, Nebraska, New Jersey,
and Pennsylvania have inheritance taxes.
"""

from dataclasses import dataclass
from typing import Dict, Optional, List
from decimal import Decimal


@dataclass
class StateTaxBracket:
    """Tax bracket for state estate/inheritance tax"""
    min_value: Decimal
    max_value: Optional[Decimal]
    rate: Decimal


class StateEstateTaxCalculator:
    """Calculate state estate and inheritance taxes"""

    # States with estate tax (as of 2024)
    ESTATE_TAX_STATES = {
        "CT", "IL", "ME", "MD", "MA", "MN", "NY", "OR", "RI", "VT", "WA", "DC"
    }

    # States with inheritance tax (applies to heirs, not estates)
    INHERITANCE_TAX_STATES = {
        "IA", "KY", "MD", "NE", "NJ", "PA"
    }

    # State exemptions (can vary by year)
    STATE_EXEMPTIONS_2024 = {
        "CT": Decimal("12920000"),
        "IL": Decimal("4000000"),
        "ME": Decimal("6750000"),
        "MD": Decimal("5000000"),
        "MA": Decimal("1000000"),
        "MN": Decimal("3600000"),
        "NY": Decimal("6940000"),
        "OR": Decimal("1000000"),
        "RI": Decimal("5.79000000"),
        "VT": Decimal("4000000"),
        "WA": Decimal("2193000"),
        "DC": Decimal("5500000"),
    }

    def __init__(self, year: int = 2024):
        self.year = year

    def calculate_state_estate_tax(
        self,
        state: str,
        taxable_estate: Decimal,
        domicile_state: str,
    ) -> Dict:
        """
        Calculate state estate tax for a given state.

        Args:
            state: Two-letter state code
            taxable_estate: Estate value after deductions
            domicile_state: State where deceased was domiciled

        Returns:
            State estate tax calculation details
        """

        state = state.upper()

        if state not in self.ESTATE_TAX_STATES:
            return {
                "state": state,
                "has_estate_tax": False,
                "state_estate_tax": Decimal(0),
                "effective_rate": Decimal(0),
            }

        exemption = self.STATE_EXEMPTIONS_2024.get(state, Decimal(0))
        taxable_amount = max(Decimal(0), taxable_estate - exemption)

        # State tax brackets (simplified example)
        tax_rate = self._get_state_tax_rate(state, taxable_amount)
        state_tax = taxable_amount * tax_rate

        return {
            "state": state,
            "has_estate_tax": True,
            "gross_taxable_estate": taxable_estate,
            "state_exemption": exemption,
            "taxable_amount": taxable_amount,
            "tax_rate": tax_rate,
            "state_estate_tax": state_tax,
            "effective_rate": (
                (state_tax / taxable_estate * 100)
                if taxable_estate > 0 else Decimal(0)
            ),
        }

    def calculate_state_inheritance_tax(
        self,
        state: str,
        heir_relationship: str,  # "spouse", "child", "sibling", "other"
        heir_share_value: Decimal,
    ) -> Dict:
        """
        Calculate state inheritance tax (applies to heir, not estate).

        Args:
            state: State with inheritance tax
            heir_relationship: Relationship of heir to deceased
            heir_share_value: Value of inheritance to this heir

        Returns:
            Inheritance tax calculation
        """

        state = state.upper()

        if state not in self.INHERITANCE_TAX_STATES:
            return {
                "state": state,
                "has_inheritance_tax": False,
                "inheritance_tax": Decimal(0),
            }

        # Get exemption and rate based on relationship
        exemption = self._get_inheritance_tax_exemption(state, heir_relationship)
        rate = self._get_inheritance_tax_rate(state, heir_relationship)

        taxable_amount = max(Decimal(0), heir_share_value - exemption)
        inheritance_tax = taxable_amount * rate

        return {
            "state": state,
            "has_inheritance_tax": True,
            "heir_relationship": heir_relationship,
            "heir_share_value": heir_share_value,
            "exemption": exemption,
            "taxable_amount": taxable_amount,
            "tax_rate": rate,
            "inheritance_tax_due": inheritance_tax,
            "heir_net_after_tax": heir_share_value - inheritance_tax,
        }

    def calculate_multi_state_estate_tax(
        self,
        taxable_estate: Decimal,
        domicile_state: str,
        real_estate_locations: Dict[str, Decimal],  # {state: value}
    ) -> Dict:
        """
        Calculate estate tax across multiple states (for multi-state property owners).

        Args:
            taxable_estate: Total taxable estate
            domicile_state: State of domicile
            real_estate_locations: Property locations and values

        Returns:
            Multi-state tax summary
        """

        total_state_tax = Decimal(0)
        state_tax_breakdown = {}

        # Domicile state taxes the entire estate
        if domicile_state in self.ESTATE_TAX_STATES:
            domicile_tax = self.calculate_state_estate_tax(
                state=domicile_state,
                taxable_estate=taxable_estate,
                domicile_state=domicile_state,
            )
            state_tax_breakdown[domicile_state] = domicile_tax
            total_state_tax += domicile_tax["state_estate_tax"]

        # Non-domicile states only tax real property located there
        for state, property_value in real_estate_locations.items():
            if state != domicile_state and state in self.ESTATE_TAX_STATES:
                state_tax = self.calculate_state_estate_tax(
                    state=state,
                    taxable_estate=property_value,
                    domicile_state=domicile_state,
                )
                state_tax_breakdown[state] = state_tax
                total_state_tax += state_tax["state_estate_tax"]

        # Calculate federal credit (if available)
        federal_credit = self._calculate_state_death_tax_credit(total_state_tax)

        return {
            "total_state_estate_tax": total_state_tax,
            "federal_credit_for_state_taxes": federal_credit,
            "net_state_tax_after_credit": max(Decimal(0), total_state_tax - federal_credit),
            "state_tax_breakdown": state_tax_breakdown,
            "properties_by_state": real_estate_locations,
        }

    @staticmethod
    def _get_state_tax_rate(state: str, taxable_amount: Decimal) -> Decimal:
        """Get state estate tax rate (simplified - rates vary by amount)"""
        state_rates = {
            "CT": Decimal("0.10"),  # Rates vary 3.6%-12%
            "IL": Decimal("0.16"),
            "ME": Decimal("0.05"),
            "MD": Decimal("0.10"),
            "MA": Decimal("0.16"),
            "MN": Decimal("0.15"),
            "NY": Decimal("0.04"),
            "OR": Decimal("0.16"),
            "RI": Decimal("0.16"),
            "VT": Decimal("0.16"),
            "WA": Decimal("0.20"),
            "DC": Decimal("0.16"),
        }
        return state_rates.get(state, Decimal(0))

    @staticmethod
    def _get_inheritance_tax_exemption(state: str, relationship: str) -> Decimal:
        """Get inheritance tax exemption based on heir relationship"""

        # Simplified exemptions (vary significantly by state)
        exemptions = {
            "PA": {
                "spouse": Decimal("0"),  # Spouse exempt
                "child": Decimal("0"),   # Child exempt
                "sibling": Decimal("3500"),
                "other": Decimal("500"),
            },
            "NJ": {
                "spouse": Decimal("0"),  # Spouse exempt
                "child": Decimal("0"),   # Child exempt
                "sibling": Decimal("25000"),
                "other": Decimal("500"),
            },
            "IA": {
                "spouse": Decimal("0"),
                "child": Decimal("0"),
                "sibling": Decimal("10000"),
                "other": Decimal("0"),
            },
        }

        return exemptions.get(state, {}).get(relationship, Decimal(0))

    @staticmethod
    def _get_inheritance_tax_rate(state: str, relationship: str) -> Decimal:
        """Get inheritance tax rate based on heir relationship"""

        rates = {
            "PA": {
                "spouse": Decimal("0"),
                "child": Decimal("0.045"),  # 4.5%
                "sibling": Decimal("0.12"),  # 12%
                "other": Decimal("0.15"),   # 15%
            },
            "NJ": {
                "spouse": Decimal("0"),
                "child": Decimal("0"),
                "sibling": Decimal("0.125"),  # 12.5%
                "other": Decimal("0.16"),    # 16%
            },
        }

        return rates.get(state, {}).get(relationship, Decimal(0))

    @staticmethod
    def _calculate_state_death_tax_credit(state_tax: Decimal) -> Decimal:
        """
        Calculate federal credit for state death taxes.

        Note: TCJA (2017) reduced this credit substantially.
        This is simplified for illustration.
        """
        # Federal credit was eliminated for deaths after 12/31/2004
        # but calculation shown for reference
        return Decimal(0)  # No current federal credit

    def check_state_tax_exposure(
        self,
        states: List[str],
        taxable_estate: Decimal,
    ) -> List[Dict]:
        """
        Check which states have estate tax exposure.

        Args:
            states: List of states where person has property
            taxable_estate: Total estate value

        Returns:
            List of states with tax exposure
        """

        exposure = []

        for state in states:
            if state.upper() in self.ESTATE_TAX_STATES:
                tax_calc = self.calculate_state_estate_tax(
                    state=state,
                    taxable_estate=taxable_estate,
                    domicile_state=state,
                )
                exposure.append(tax_calc)

        return exposure


# Special tax consideration rules

def calculate_credit_for_prior_transfer_tax(
    previous_estate_tax: Decimal,
    years_between_deaths: int,
) -> Decimal:
    """
    Calculate federal credit for taxes paid on prior transfer.

    Args:
        previous_estate_tax: Estate tax paid by first spouse
        years_between_deaths: Years between first and second death

    Returns:
        Credit available (phases out after 10 years)
    """

    # Credit reduces linearly from 100% to 0% over 10-year period
    if years_between_deaths > 10:
        return Decimal(0)

    percentage = Decimal(100 - (years_between_deaths * 10)) / Decimal(100)
    return previous_estate_tax * percentage


def calculate_state_tax_apportionment(
    state_estate_tax: Decimal,
    federal_estate_tax: Decimal,
    assets_to_beneficiary: Decimal,
    total_taxable_estate: Decimal,
) -> Dict:
    """
    Calculate apportionment of state taxes to beneficiaries.

    Args:
        state_estate_tax: Total state tax due
        federal_estate_tax: Total federal tax due
        assets_to_beneficiary: Value of assets to specific beneficiary
        total_taxable_estate: Total taxable estate

    Returns:
        Tax apportionment to beneficiary
    """

    # Proportional apportionment
    beneficiary_percentage = (
        assets_to_beneficiary / total_taxable_estate
        if total_taxable_estate > 0 else Decimal(0)
    )

    apportioned_state_tax = state_estate_tax * beneficiary_percentage
    apportioned_federal_tax = federal_estate_tax * beneficiary_percentage
    total_taxes = apportioned_state_tax + apportioned_federal_tax

    beneficiary_net = assets_to_beneficiary - total_taxes

    return {
        "asset_value": assets_to_beneficiary,
        "percentage_of_estate": beneficiary_percentage * 100,
        "apportioned_state_tax": apportioned_state_tax,
        "apportioned_federal_tax": apportioned_federal_tax,
        "total_taxes_apportioned": total_taxes,
        "net_to_beneficiary": beneficiary_net,
    }
