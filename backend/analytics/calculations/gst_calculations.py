"""
Generation-Skipping Transfer (GST) Tax Calculations

Handles calculation of GST tax and exemption tracking for:
- Direct skips (transfers directly to skip persons)
- Taxable terminations (distribution from trust to skip person)
- Taxable distributions (distribution from trust to non-skip person)
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from decimal import Decimal
from enum import Enum


class GenerationLevel(Enum):
    """Generation levels for GST tax purposes"""
    GENERATION_0 = "grandparent"  # Transferor
    GENERATION_1 = "parent"
    GENERATION_2 = "grandchild"
    GENERATION_3 = "great_grandchild"


@dataclass
class GSTAllocationDetail:
    """Details of GST exemption allocation"""
    beneficiary_name: str
    generation_level: int
    amount_allocated: Decimal
    amount_used: Decimal
    amount_remaining: Decimal


class GSTExemptionTracker:
    """
    Track GST exemption usage and optimize allocation.

    Each person receives a lifetime GST exemption.
    """

    # GST exemptions by year (same as federal estate tax exemption)
    GST_EXEMPTIONS = {
        2020: Decimal("11580000"),
        2021: Decimal("11700000"),
        2022: Decimal("12060000"),
        2023: Decimal("12920000"),
        2024: Decimal("13610000"),
        2025: Decimal("13990000"),
    }

    def __init__(self, year: int = 2024):
        self.year = year
        self.exemption_amount = self._get_gst_exemption(year)

    @staticmethod
    def _get_gst_exemption(year: int) -> Decimal:
        """Get GST exemption for a given year"""
        return GSTExemptionTracker.GST_EXEMPTIONS.get(year, Decimal("13610000"))

    def determine_generation_level(
        self,
        transferor_birth_year: int,
        beneficiary_birth_year: int,
    ) -> int:
        """
        Determine generation level for GST tax purposes.

        Returns:
            0 = Transferor (same generation as transferor)
            1 = Direct descendants (children)
            2 = Grandchildren
            3+ = More distant descendants
        """

        # Special rule: persons not more than 37.5 years younger = same generation
        age_difference = beneficiary_birth_year - transferor_birth_year

        if age_difference <= -37.5 or beneficiary_birth_year >= transferor_birth_year:
            # Older or same age = same generation
            return 0
        elif -75 < age_difference < -37.5:
            return 1
        elif -112.5 < age_difference <= -75:
            return 2
        else:
            # More than 3 generations
            return (age_difference // -37.5).__int__()

    def is_skip_person(
        self,
        generation_level: int,
        transferor_generation_level: int = 0,
    ) -> bool:
        """
        Determine if beneficiary is a skip person (more than one generation below transferor).

        Args:
            generation_level: Beneficiary's generation level relative to transferor
            transferor_generation_level: Transferor's generation (always 0)

        Returns:
            True if beneficiary is skip person
        """
        return generation_level > 1

    def calculate_gst_tax(
        self,
        transfer_amount: Decimal,
        gst_exemption_used: Decimal,
        is_direct_skip: bool,
        is_taxable_termination: bool = False,
    ) -> Dict:
        """
        Calculate GST tax on a transfer to skip persons.

        Args:
            transfer_amount: Value of property transferred
            gst_exemption_used: Amount of exemption already used by transferor
            is_direct_skip: Whether this is a direct skip transfer
            is_taxable_termination: Whether this is a taxable termination

        Returns:
            GST tax calculation details
        """

        exemption_remaining = self.exemption_amount - gst_exemption_used
        gst_taxable_amount = max(Decimal(0), transfer_amount - exemption_remaining)

        # GST tax rate is highest estate tax rate (40% in 2024)
        gst_tax_rate = Decimal("0.40")
        gst_tax_due = gst_taxable_amount * gst_tax_rate

        return {
            "transfer_amount": transfer_amount,
            "gst_exemption_available": self.exemption_amount,
            "gst_exemption_used_to_date": gst_exemption_used,
            "gst_exemption_remaining": exemption_remaining,
            "gst_taxable_amount": gst_taxable_amount,
            "gst_tax_rate": gst_tax_rate,
            "gst_tax_due": gst_tax_due,
            "is_direct_skip": is_direct_skip,
            "is_taxable_termination": is_taxable_termination,
            "inclusion_ratio": self._calculate_inclusion_ratio(
                gst_taxable_amount,
                transfer_amount
            ),
        }

    def allocate_gst_exemption_optimally(
        self,
        beneficiaries: List[Dict],  # [{name, value, generation_level}, ...]
        available_exemption: Decimal,
    ) -> Dict:
        """
        Allocate GST exemption to minimize overall GST tax.

        Optimal strategy prioritizes allocation to:
        1. Skip persons (must use exemption or pay GST tax)
        2. High-value transfers
        3. Assets with growth potential

        Args:
            beneficiaries: List of beneficiaries with values
            available_exemption: Available exemption amount

        Returns:
            Optimal allocation strategy
        """

        # Sort by value (allocate to highest value transfers first)
        sorted_beneficiaries = sorted(
            beneficiaries,
            key=lambda x: x.get("value", Decimal(0)),
            reverse=True
        )

        allocations = []
        remaining_exemption = available_exemption
        total_gst_tax_saved = Decimal(0)

        for beneficiary in sorted_beneficiaries:
            value = Decimal(str(beneficiary.get("value", 0)))
            generation_level = beneficiary.get("generation_level", 0)

            # Allocate exemption if skip person
            if generation_level > 1 and remaining_exemption > 0:
                allocation = min(remaining_exemption, value)
                remaining_exemption -= allocation

                gst_taxable = max(Decimal(0), value - allocation)
                gst_tax_saved = gst_taxable * Decimal("0.40")

                allocations.append({
                    "beneficiary": beneficiary.get("name"),
                    "transfer_value": value,
                    "generation_level": generation_level,
                    "gst_exemption_allocated": allocation,
                    "gst_taxable_amount": gst_taxable,
                    "gst_tax_that_would_apply": gst_tax_saved,
                })

                total_gst_tax_saved += gst_tax_saved

        return {
            "allocations": allocations,
            "total_exemption_allocated": available_exemption - remaining_exemption,
            "exemption_remaining": remaining_exemption,
            "estimated_gst_tax_savings": total_gst_tax_saved,
        }

    def calculate_direct_skip_tax(
        self,
        transfer_value: Decimal,
        gst_exemption_available: Decimal,
    ) -> Dict:
        """
        Calculate tax on direct skip transfer (transfer to skip person).

        Includes both gift tax and GST tax considerations.

        Args:
            transfer_value: Value transferred
            gst_exemption_available: Available GST exemption

        Returns:
            Direct skip tax calculation
        """

        gst_tax_calc = self.calculate_gst_tax(
            transfer_amount=transfer_value,
            gst_exemption_used=self.exemption_amount - gst_exemption_available,
            is_direct_skip=True,
        )

        return {
            **gst_tax_calc,
            "transfer_type": "direct_skip",
        }

    def calculate_taxable_termination_tax(
        self,
        trust_value_at_termination: Decimal,
        gst_exemption_allocated_to_trust: Decimal,
        trust_tax_rate: Decimal = Decimal("0.40"),
    ) -> Dict:
        """
        Calculate GST tax on taxable termination (when trust ends and passes to skip persons).

        Args:
            trust_value_at_termination: Value of trust when it terminates
            gst_exemption_allocated_to_trust: GST exemption allocated to trust
            trust_tax_rate: Applicable tax rate

        Returns:
            Taxable termination tax calculation
        """

        # GST tax on termination
        gst_taxable_amount = max(
            Decimal(0),
            trust_value_at_termination - gst_exemption_allocated_to_trust
        )

        gst_tax = gst_taxable_amount * trust_tax_rate

        return {
            "trust_value_at_termination": trust_value_at_termination,
            "gst_exemption_allocated": gst_exemption_allocated_to_trust,
            "gst_taxable_amount": gst_taxable_amount,
            "gst_tax_rate": trust_tax_rate,
            "gst_tax_due": gst_tax,
            "transfer_type": "taxable_termination",
            "inclusion_ratio": self._calculate_inclusion_ratio(
                gst_taxable_amount,
                trust_value_at_termination
            ),
        }

    def calculate_taxable_distribution_tax(
        self,
        distribution_amount: Decimal,
        trust_inclusion_ratio: Decimal,
    ) -> Dict:
        """
        Calculate GST tax on taxable distribution (distribution to non-skip person
        from trust that has skip persons as beneficiaries).

        Args:
            distribution_amount: Amount distributed
            trust_inclusion_ratio: Inclusion ratio of trust

        Returns:
            Taxable distribution tax calculation
        """

        gst_taxable_amount = distribution_amount * trust_inclusion_ratio
        gst_tax_rate = Decimal("0.40")
        gst_tax = gst_taxable_amount * gst_tax_rate

        return {
            "distribution_amount": distribution_amount,
            "trust_inclusion_ratio": trust_inclusion_ratio,
            "gst_taxable_amount": gst_taxable_amount,
            "gst_tax_rate": gst_tax_rate,
            "gst_tax_due": gst_tax,
            "transfer_type": "taxable_distribution",
        }

    def calculate_dynasty_trust_impact(
        self,
        initial_trust_value: Decimal,
        gst_exemption_allocated: Decimal,
        annual_growth_rate: Decimal = Decimal("0.06"),
        years: int = 50,
    ) -> Dict:
        """
        Calculate multi-generational impact of dynasty trust funded with GST exemption.

        Args:
            initial_trust_value: Initial funding amount
            gst_exemption_allocated: GST exemption allocated to trust
            annual_growth_rate: Assumed annual growth rate
            years: Years to project

        Returns:
            Dynasty trust projection
        """

        # Project growth over time
        projected_value = initial_trust_value
        for year in range(years):
            projected_value = projected_value * (1 + annual_growth_rate)

        # Without exemption allocation
        exemption_value_without_allocation = (
            (initial_trust_value - gst_exemption_allocated) * Decimal("0.40")
        )

        # Tax saved with exemption allocation
        # (potential GST taxes on appreciation)
        appreciation = projected_value - initial_trust_value
        potential_gst_on_appreciation = appreciation * Decimal("0.40")

        return {
            "initial_trust_funding": initial_trust_value,
            "gst_exemption_allocated": gst_exemption_allocated,
            "projected_value_after_years": projected_value,
            "years_projected": years,
            "total_appreciation": appreciation,
            "estimated_gst_tax_avoided": (
                (initial_trust_value - gst_exemption_allocated) * Decimal("0.40")
                + potential_gst_on_appreciation
            ),
            "generation_skipping_benefit": "Tax-free to multiple generations",
        }

    @staticmethod
    def _calculate_inclusion_ratio(
        gst_taxable_amount: Decimal,
        transfer_amount: Decimal,
    ) -> Decimal:
        """
        Calculate inclusion ratio for GST tax purposes.

        Used to determine ongoing GST tax on trust distributions.
        """
        if transfer_amount <= 0:
            return Decimal(0)

        return gst_taxable_amount / transfer_amount


def calculate_gst_exemption_for_married_couple(
    husband_exemption_used: Decimal,
    wife_exemption_used: Decimal,
    current_year: int = 2024,
) -> Dict:
    """
    Calculate combined GST exemption for married couple.

    Args:
        husband_exemption_used: Husband's exemption used to date
        wife_exemption_used: Wife's exemption used to date
        current_year: Tax year

    Returns:
        Combined exemption availability
    """

    exemptions_2024 = {
        2024: Decimal("13610000"),
    }

    annual_exemption = exemptions_2024.get(current_year, Decimal("13610000"))

    husband_available = annual_exemption - husband_exemption_used
    wife_available = annual_exemption - wife_exemption_used
    combined_available = husband_available + wife_available

    return {
        "husband_total_exemption": annual_exemption,
        "husband_exemption_used": husband_exemption_used,
        "husband_exemption_remaining": husband_available,
        "wife_total_exemption": annual_exemption,
        "wife_exemption_used": wife_exemption_used,
        "wife_exemption_remaining": wife_available,
        "combined_exemption_available": combined_available,
        "potential_gst_taxes_avoided": combined_available * Decimal("0.40"),
    }
