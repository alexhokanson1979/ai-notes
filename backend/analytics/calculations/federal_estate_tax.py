"""
Federal Estate Tax Calculation Engine

Handles calculation of federal estate tax including:
- Taxable estate determination
- Exemption application
- Marital and charitable deductions
- Step-up in basis
- QLTS (Qualified Terminable Interest Property) trusts
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import datetime


@dataclass
class FederalEstateTaxBracket:
    """Tax bracket for federal estate tax"""
    min_value: Decimal
    max_value: Optional[Decimal]
    rate: Decimal
    base_tax: Decimal = Decimal(0)


class FederalEstateTaxCalculator:
    """
    Calculate federal estate tax based on current law.

    Tax brackets and exemptions update annually (indexed to inflation).
    """

    # 2024 Tax brackets (unified estate and gift tax)
    # Federal estate tax is a flat 40% on amount exceeding exemption
    FEDERAL_TAX_RATE_2024 = Decimal("0.40")
    FEDERAL_EXEMPTION_2024 = Decimal("13610000")  # $13.61M
    ANNUAL_EXCLUSION_2024 = Decimal("18000")  # Indexed annually

    # State where estate is domiciled (affects portability, etc.)
    # Federal tax applies regardless of state

    def __init__(self, year: int = 2024):
        """Initialize calculator for a specific tax year"""
        self.year = year
        self.exemption = self._get_exemption_for_year(year)
        self.annual_exclusion = self._get_annual_exclusion_for_year(year)
        self.tax_rate = Decimal("0.40")

    @staticmethod
    def _get_exemption_for_year(year: int) -> Decimal:
        """Get federal estate tax exemption for a given year"""
        exemptions = {
            2020: Decimal("11580000"),
            2021: Decimal("11700000"),
            2022: Decimal("12060000"),
            2023: Decimal("12920000"),
            2024: Decimal("13610000"),
            2025: Decimal("13990000"),
        }
        return exemptions.get(year, Decimal("13610000"))

    @staticmethod
    def _get_annual_exclusion_for_year(year: int) -> Decimal:
        """Get annual gift tax exclusion for a given year"""
        exclusions = {
            2020: Decimal("15000"),
            2021: Decimal("15000"),
            2022: Decimal("16000"),
            2023: Decimal("17000"),
            2024: Decimal("18000"),
            2025: Decimal("18000"),
        }
        return exclusions.get(year, Decimal("18000"))

    def calculate_federal_estate_tax(
        self,
        gross_estate: Decimal,
        marital_deduction: Decimal = Decimal(0),
        charitable_deduction: Decimal = Decimal(0),
        administration_expenses: Decimal = Decimal(0),
        available_exemption: Decimal = None,
        portability_used: bool = False,
        spouse_exemption_available: Decimal = None,
    ) -> Dict:
        """
        Calculate federal estate tax for an estate.

        Args:
            gross_estate: Total value of all assets
            marital_deduction: Amount passing to surviving spouse (unlimited deduction)
            charitable_deduction: Amount to qualified charities (unlimited deduction)
            administration_expenses: Executor fees, attorney fees, etc.
            available_exemption: Portion of lifetime exemption not yet used
            portability_used: Whether to use portability with spouse
            spouse_exemption_available: Spouse's unused exemption (if portability)

        Returns:
            Dictionary with detailed tax calculation breakdown
        """

        # Calculate taxable estate
        taxable_estate = self._calculate_taxable_estate(
            gross_estate=gross_estate,
            marital_deduction=marital_deduction,
            charitable_deduction=charitable_deduction,
            administration_expenses=administration_expenses,
        )

        # Determine applicable exclusion
        if available_exemption is None:
            available_exemption = self.exemption

        # Apply portability if available
        applicable_exemption = available_exemption
        if portability_used and spouse_exemption_available:
            applicable_exemption = available_exemption + spouse_exemption_available

        # Calculate taxable amount (taxable estate minus exemption)
        taxable_amount = max(Decimal(0), taxable_estate - applicable_exemption)

        # Calculate estate tax
        federal_estate_tax = taxable_amount * self.tax_rate

        return {
            "gross_estate": gross_estate,
            "marital_deduction": marital_deduction,
            "charitable_deduction": charitable_deduction,
            "administration_expenses": administration_expenses,
            "taxable_estate": taxable_estate,
            "applicable_exemption": applicable_exemption,
            "taxable_amount": taxable_amount,
            "federal_estate_tax": federal_estate_tax,
            "effective_tax_rate": (
                (federal_estate_tax / gross_estate * 100)
                if gross_estate > 0 else Decimal(0)
            ),
            "net_to_heirs": gross_estate - federal_estate_tax,
            "year": self.year,
            "portability_applied": portability_used,
        }

    def _calculate_taxable_estate(
        self,
        gross_estate: Decimal,
        marital_deduction: Decimal,
        charitable_deduction: Decimal,
        administration_expenses: Decimal,
    ) -> Decimal:
        """Calculate the taxable estate after deductions"""
        taxable_estate = (
            gross_estate
            - marital_deduction
            - charitable_deduction
            - administration_expenses
        )
        return max(Decimal(0), taxable_estate)

    def apply_marital_deduction(
        self,
        assets_to_spouse: Decimal,
        qualifies_for_qprt: bool = False,
        qualifies_for_qdot: bool = False,
    ) -> Decimal:
        """
        Apply marital deduction for assets passing to surviving spouse.

        Args:
            assets_to_spouse: Value of assets passing to spouse
            qualifies_for_qprt: Whether using QDOT (spouse not US citizen)
            qualifies_for_qdot: Whether using QPRT

        Returns:
            Amount of marital deduction allowed
        """
        # Unlimited marital deduction if spouse is US citizen
        if not qualifies_for_qdot:
            return assets_to_spouse

        # QDOT limitations for non-citizen spouse
        # This is simplified; QDOT has complex rules
        if qualifies_for_qdot:
            return assets_to_spouse

        return assets_to_spouse

    def calculate_step_up_in_basis(
        self,
        asset_cost_basis: Decimal,
        asset_fair_market_value: Decimal,
        inside_irrevocable_trust: bool = False,
        joint_tenancy_percentage: Decimal = Decimal(0),
    ) -> Dict:
        """
        Calculate step-up in basis for inherited property.

        Args:
            asset_cost_basis: Original cost basis of asset
            asset_fair_market_value: FMV at death
            inside_irrevocable_trust: Whether asset in irrevocable trust
            joint_tenancy_percentage: Percentage owned as joint tenant

        Returns:
            Basis calculation details
        """

        # Step-up basis = FMV at death
        # Only applies to assets included in taxable estate
        if inside_irrevocable_trust:
            # Assets in ILIT not included in estate
            stepped_up_basis = asset_cost_basis
            basis_increase = Decimal(0)
        else:
            stepped_up_basis = asset_fair_market_value
            basis_increase = max(Decimal(0), asset_fair_market_value - asset_cost_basis)

        # Apply joint tenancy limitation
        if joint_tenancy_percentage > Decimal(0):
            # Only own portion steps up
            stepped_up_basis = (
                asset_cost_basis
                + (basis_increase * joint_tenancy_percentage)
            )

        future_capital_gains_tax_avoided = basis_increase * Decimal("0.20")  # 20% LTCG rate

        return {
            "original_cost_basis": asset_cost_basis,
            "fair_market_value_at_death": asset_fair_market_value,
            "stepped_up_basis": stepped_up_basis,
            "basis_increase": basis_increase,
            "estimated_capital_gains_tax_avoided": future_capital_gains_tax_avoided,
        }

    def calculate_irrevocable_life_insurance_trust_impact(
        self,
        insurance_face_value: Decimal,
        years_until_death: int = 3,
    ) -> Dict:
        """
        Calculate tax impact of holding life insurance in ILIT.

        Args:
            insurance_face_value: Death benefit
            years_until_death: Years until insured's death (affects 3-year rule)

        Returns:
            Tax savings from ILIT strategy
        """

        # If death within 3 years of transfer, included in estate
        # Otherwise, proceeds excluded
        if years_until_death <= 3:
            estate_inclusion = insurance_face_value
        else:
            estate_inclusion = Decimal(0)

        tax_savings = (
            (insurance_face_value - estate_inclusion) * self.tax_rate
        )

        return {
            "insurance_face_value": insurance_face_value,
            "estate_inclusion": estate_inclusion,
            "estate_exclusion": insurance_face_value - estate_inclusion,
            "estate_tax_savings": tax_savings,
            "within_three_year_rule": years_until_death <= 3,
        }

    def calculate_annual_gift_tax_savings(
        self,
        annual_gifts_per_beneficiary: Decimal,
        number_of_beneficiaries: int,
    ) -> Dict:
        """
        Calculate tax savings from annual exclusion gifts.

        Args:
            annual_gifts_per_beneficiary: Amount gifted to each person
            number_of_beneficiaries: Number of people receiving gifts

        Returns:
            Tax savings from gifting strategy
        """

        total_gifts = annual_gifts_per_beneficiary * number_of_beneficiaries
        non_excluded_amount = max(
            Decimal(0),
            annual_gifts_per_beneficiary - self.annual_exclusion
        )

        # Gifts use lifetime exemption if above annual exclusion
        exemption_used = non_excluded_amount * number_of_beneficiaries

        future_estate_tax_savings = (
            total_gifts * self.tax_rate
        )

        return {
            "total_annual_gifts": total_gifts,
            "annual_exclusion_per_person": self.annual_exclusion,
            "excluded_gifts": min(
                total_gifts,
                self.annual_exclusion * number_of_beneficiaries
            ),
            "taxable_gifts": max(
                Decimal(0),
                total_gifts - (self.annual_exclusion * number_of_beneficiaries)
            ),
            "lifetime_exemption_used": exemption_used,
            "estimated_future_estate_tax_savings": future_estate_tax_savings,
        }

    def calculate_charitable_deduction_impact(
        self,
        charitable_remainder_trust_value: Decimal,
        charitable_lead_trust_value: Decimal,
        outright_charity: Decimal,
    ) -> Dict:
        """
        Calculate impact of charitable giving strategies.

        Args:
            charitable_remainder_trust_value: Amount in CRT (passes to charity after term)
            charitable_lead_trust_value: Amount in CLT (charity gets income first)
            outright_charity: Direct bequests to charity

        Returns:
            Deduction and tax savings details
        """

        total_charitable_deduction = (
            charitable_remainder_trust_value
            + charitable_lead_trust_value
            + outright_charity
        )

        estate_tax_savings = total_charitable_deduction * self.tax_rate

        return {
            "charitable_remainder_trust": charitable_remainder_trust_value,
            "charitable_lead_trust": charitable_lead_trust_value,
            "outright_charitable_gifts": outright_charity,
            "total_charitable_deduction": total_charitable_deduction,
            "estate_tax_savings": estate_tax_savings,
            "combined_estate_and_income_tax_savings": estate_tax_savings,  # Simplified
        }

    def calculate_grantor_retained_annuity_trust(
        self,
        trust_asset_value: Decimal,
        annual_annuity_payment: Decimal,
        trust_term_years: int,
        discount_rate: Decimal = Decimal("0.03"),
    ) -> Dict:
        """
        Calculate GRAT impact on estate tax.

        Args:
            trust_asset_value: Initial value of assets in GRAT
            annual_annuity_payment: Payment to grantor each year
            trust_term_years: Length of GRAT term
            discount_rate: IRS 7520 discount rate

        Returns:
            Estate inclusion and savings calculations
        """

        # Simplified GRAT calculation
        # Present value of annuity stream
        annuity_pv = self._calculate_annuity_pv(
            annual_payment=annual_annuity_payment,
            years=trust_term_years,
            discount_rate=discount_rate,
        )

        # Taxable gift = FMV - PV of annuity
        taxable_gift = max(Decimal(0), trust_asset_value - annuity_pv)

        # Remainder goes to beneficiaries, not included in gross estate
        remainder_value = trust_asset_value - annuity_pv

        estate_tax_savings = remainder_value * self.tax_rate

        return {
            "initial_trust_asset_value": trust_asset_value,
            "present_value_of_annuity": annuity_pv,
            "taxable_gift": taxable_gift,
            "gift_tax_due_if_no_exemption": taxable_gift * self.tax_rate,
            "remainder_to_beneficiaries": remainder_value,
            "estimated_estate_tax_savings": estate_tax_savings,
            "assumes_appreciation_in_remainder": "Actual savings depend on asset appreciation",
        }

    @staticmethod
    def _calculate_annuity_pv(
        annual_payment: Decimal,
        years: int,
        discount_rate: Decimal,
    ) -> Decimal:
        """Calculate present value of annuity payments"""
        pv = Decimal(0)
        for year in range(1, years + 1):
            pv += annual_payment / ((1 + discount_rate) ** year)
        return pv
