"""
SQLAlchemy database models for the Financial Planning Application.
"""

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean,
    ForeignKey, Text, Enum, JSON, Date, Numeric
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

Base = declarative_base()


# ============================================================================
# CLIENT & ESTATE ENTITIES
# ============================================================================

class Client(Base):
    """Core client/household entity"""
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20))
    organization = Column(String(255))  # For white-label
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    estates = relationship("Estate", back_populates="client")
    presentations = relationship("Presentation", back_populates="client")


class Estate(Base):
    """Primary estate entity"""
    __tablename__ = "estates"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    primary_owner_name = Column(String(255), nullable=False)
    spouse_name = Column(String(255))
    total_assets_value = Column(Numeric(15, 2), default=0)
    created_date = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text)

    client = relationship("Client", back_populates="estates")
    family_members = relationship("FamilyMember", back_populates="estate", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="estate", cascade="all, delete-orphan")
    insurance_policies = relationship("LifeInsurancePolicy", back_populates="estate", cascade="all, delete-orphan")
    estate_plans = relationship("EstatePlan", back_populates="estate", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="estate", cascade="all, delete-orphan")
    promissory_notes = relationship("PromissoryNote", back_populates="estate", cascade="all, delete-orphan")
    gift_transactions = relationship("GiftTransaction", back_populates="estate", cascade="all, delete-orphan")
    gst_allocations = relationship("GSTAllocation", back_populates="estate", cascade="all, delete-orphan")


# ============================================================================
# FAMILY MANAGEMENT
# ============================================================================

class RelationshipType(PyEnum):
    SPOUSE = "spouse"
    CHILD = "child"
    GRANDCHILD = "grandchild"
    PARENT = "parent"
    SIBLING = "sibling"
    OTHER = "other"


class FamilyMember(Base):
    """Family members and beneficiaries"""
    __tablename__ = "family_members"

    id = Column(Integer, primary_key=True)
    estate_id = Column(Integer, ForeignKey("estates.id"), nullable=False)
    name = Column(String(255), nullable=False)
    relationship = Column(Enum(RelationshipType), nullable=False)
    date_of_birth = Column(Date)
    date_of_death = Column(Date)
    is_alive = Column(Boolean, default=True)
    ssn = Column(String(11))  # Encrypted in production
    generation_level = Column(Integer, default=1)  # For GST tracking
    notes = Column(Text)

    estate = relationship("Estate", back_populates="family_members")
    beneficiary_allocations = relationship("AssetAllocation", back_populates="beneficiary")
    gst_allocations = relationship("GSTAllocation", back_populates="beneficiary")


class FamilyTree(Base):
    """Hierarchical family relationships"""
    __tablename__ = "family_trees"

    id = Column(Integer, primary_key=True)
    estate_id = Column(Integer, ForeignKey("estates.id"))
    parent_id = Column(Integer, ForeignKey("family_members.id"))
    child_id = Column(Integer, ForeignKey("family_members.id"))

    parent = relationship("FamilyMember", foreign_keys=[parent_id])
    child = relationship("FamilyMember", foreign_keys=[child_id])


# ============================================================================
# ASSET MANAGEMENT
# ============================================================================

class AssetType(PyEnum):
    REAL_ESTATE = "real_estate"
    STOCKS = "stocks"
    BONDS = "bonds"
    CASH = "cash"
    BUSINESS_INTEREST = "business_interest"
    RETIREMENT_ACCOUNT = "retirement_account"
    LIFE_INSURANCE = "life_insurance"
    ARTWORK = "artwork"
    VEHICLE = "vehicle"
    JEWELRY = "jewelry"
    OTHER = "other"


class OwnershipType(PyEnum):
    INDIVIDUAL = "individual"
    JOINT_TENANTS = "joint_tenants"
    TENANTS_IN_COMMON = "tenants_in_common"
    COMMUNITY_PROPERTY = "community_property"
    TRUST = "trust"
    CORPORATION = "corporation"
    PARTNERSHIP = "partnership"


class Asset(Base):
    """Individual asset holdings"""
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True)
    estate_id = Column(Integer, ForeignKey("estates.id"), nullable=False)
    description = Column(String(255), nullable=False)
    asset_type = Column(Enum(AssetType), nullable=False)
    current_value = Column(Numeric(15, 2), nullable=False)
    date_acquired = Column(Date)
    cost_basis = Column(Numeric(15, 2))
    ownership_type = Column(Enum(OwnershipType), default=OwnershipType.INDIVIDUAL)
    ownership_percentage = Column(Float, default=100.0)
    location = Column(String(255))  # For real estate, multi-state tracking
    deferred_taxes = Column(Numeric(15, 2), default=0)
    notes = Column(Text)
    created_date = Column(DateTime, default=datetime.utcnow)

    estate = relationship("Estate", back_populates="assets")
    allocations = relationship("AssetAllocation", back_populates="asset", cascade="all, delete-orphan")


class AssetAllocation(Base):
    """How assets pass to beneficiaries"""
    __tablename__ = "asset_allocations"

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    beneficiary_id = Column(Integer, ForeignKey("family_members.id"), nullable=False)
    allocation_percentage = Column(Float, nullable=False)
    allocation_method = Column(String(50))  # "outright", "trust", "conditional"
    condition = Column(Text)  # e.g., "at age 25"

    asset = relationship("Asset", back_populates="allocations")
    beneficiary = relationship("FamilyMember", back_populates="beneficiary_allocations")


class LifeInsurancePolicy(Base):
    """Life insurance tracking"""
    __tablename__ = "life_insurance_policies"

    id = Column(Integer, primary_key=True)
    estate_id = Column(Integer, ForeignKey("estates.id"), nullable=False)
    insured_name = Column(String(255), nullable=False)
    policy_number = Column(String(50), unique=True)
    face_value = Column(Numeric(15, 2), nullable=False)
    cash_surrender_value = Column(Numeric(15, 2), default=0)
    annual_premium = Column(Numeric(10, 2), nullable=False)
    policy_owner = Column(String(255))
    beneficiary = Column(String(255))
    policy_type = Column(String(50))  # "term", "whole", "universal", "variable"
    issue_date = Column(Date)
    maturity_date = Column(Date)
    is_irrevocable_trust_owned = Column(Boolean, default=False)
    notes = Column(Text)

    estate = relationship("Estate", back_populates="insurance_policies")


class PromissoryNote(Base):
    """Track loans, notes, and mortgages"""
    __tablename__ = "promissory_notes"

    id = Column(Integer, primary_key=True)
    estate_id = Column(Integer, ForeignKey("estates.id"), nullable=False)
    description = Column(String(255), nullable=False)
    creditor = Column(String(255), nullable=False)
    debtor = Column(String(255), nullable=False)
    principal_amount = Column(Numeric(15, 2), nullable=False)
    interest_rate = Column(Float, nullable=False)  # Percentage
    term_months = Column(Integer, nullable=False)
    monthly_payment = Column(Numeric(10, 2), nullable=False)
    start_date = Column(Date, nullable=False)
    maturity_date = Column(Date, nullable=False)
    remaining_balance = Column(Numeric(15, 2), nullable=False)
    payment_frequency = Column(String(20))  # "monthly", "quarterly", "annual"
    notes = Column(Text)

    estate = relationship("Estate", back_populates="promissory_notes")
    amortization_schedule = relationship("AmortizationSchedule", back_populates="note", cascade="all, delete-orphan")


class AmortizationSchedule(Base):
    """Payment schedule for loans and notes"""
    __tablename__ = "amortization_schedules"

    id = Column(Integer, primary_key=True)
    note_id = Column(Integer, ForeignKey("promissory_notes.id"), nullable=False)
    payment_number = Column(Integer, nullable=False)
    payment_date = Column(Date, nullable=False)
    payment_amount = Column(Numeric(10, 2), nullable=False)
    principal_payment = Column(Numeric(10, 2), nullable=False)
    interest_payment = Column(Numeric(10, 2), nullable=False)
    remaining_balance = Column(Numeric(15, 2), nullable=False)

    note = relationship("PromissoryNote", back_populates="amortization_schedule")


# ============================================================================
# TAX & EXEMPTION TRACKING
# ============================================================================

class TaxRate(Base):
    """Tax rates configuration by year and jurisdiction"""
    __tablename__ = "tax_rates"

    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    jurisdiction = Column(String(50), nullable=False)  # "federal", "CA", "NY", etc.
    estate_tax_rate = Column(Float)  # Can be tiered
    gift_tax_rate = Column(Float)
    exemption_amount = Column(Numeric(15, 2))
    annual_exclusion = Column(Numeric(10, 2))  # Annual gift tax exclusion
    effective_date = Column(Date)
    notes = Column(Text)

    __table_args__ = (
        # Ensure only one entry per year/jurisdiction
    )


class GiftTransaction(Base):
    """Track gifts for exemption purposes"""
    __tablename__ = "gift_transactions"

    id = Column(Integer, primary_key=True)
    estate_id = Column(Integer, ForeignKey("estates.id"), nullable=False)
    gift_date = Column(Date, nullable=False)
    donor = Column(String(255), nullable=False)
    recipient = Column(String(255), nullable=False)
    gift_amount = Column(Numeric(15, 2), nullable=False)
    applies_to_annual_exclusion = Column(Boolean, default=True)
    applies_to_lifetime_exemption = Column(Boolean, default=False)
    gift_type = Column(String(50))  # "cash", "securities", "property", etc.
    notes = Column(Text)

    estate = relationship("Estate", back_populates="gift_transactions")


class GSTAllocation(Base):
    """Track Generation-Skipping Transfer exemption usage"""
    __tablename__ = "gst_allocations"

    id = Column(Integer, primary_key=True)
    estate_id = Column(Integer, ForeignKey("estates.id"), nullable=False)
    beneficiary_id = Column(Integer, ForeignKey("family_members.id"), nullable=False)
    allocation_year = Column(Integer, nullable=False)
    exemption_allocated = Column(Numeric(15, 2), nullable=False)
    exemption_used = Column(Numeric(15, 2), default=0)
    allocation_method = Column(String(50))  # "trust", "direct", "estate"
    notes = Column(Text)

    estate = relationship("Estate", back_populates="gst_allocations")
    beneficiary = relationship("FamilyMember", back_populates="gst_allocations")


# ============================================================================
# ESTATE PLANNING & SCENARIOS
# ============================================================================

class EstatePlan(Base):
    """Primary estate plan document"""
    __tablename__ = "estate_plans"

    id = Column(Integer, primary_key=True)
    estate_id = Column(Integer, ForeignKey("estates.id"), nullable=False)
    plan_name = Column(String(255), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)
    updated_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    total_estate_value = Column(Numeric(15, 2))
    estimated_estate_tax = Column(Numeric(15, 2))
    estimated_net_to_heirs = Column(Numeric(15, 2))
    distribution_summary = Column(JSON)  # Structured distribution plan
    is_current = Column(Boolean, default=True)
    notes = Column(Text)

    estate = relationship("Estate", back_populates="estate_plans")
    scenarios = relationship("Scenario", back_populates="estate_plan", cascade="all, delete-orphan")


class Scenario(Base):
    """Planning scenario/variant"""
    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True)
    estate_plan_id = Column(Integer, ForeignKey("estate_plans.id"), nullable=False)
    scenario_name = Column(String(255), nullable=False)
    description = Column(Text)
    created_date = Column(DateTime, default=datetime.utcnow)
    is_baseline = Column(Boolean, default=False)

    estate_plan = relationship("EstatePlan", back_populates="scenarios")
    variables = relationship("ScenarioVariable", back_populates="scenario", cascade="all, delete-orphan")
    results = relationship("ScenarioResult", back_populates="scenario", cascade="all, delete-orphan")


class ScenarioVariable(Base):
    """Variables for scenario modeling"""
    __tablename__ = "scenario_variables"

    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"), nullable=False)
    variable_name = Column(String(100), nullable=False)
    variable_type = Column(String(50))  # "asset_value", "tax_rate", "life_expectancy", etc.
    base_value = Column(String(255))
    scenario_value = Column(String(255))
    impact_description = Column(Text)

    scenario = relationship("Scenario", back_populates="variables")


class ScenarioResult(Base):
    """Results from scenario simulations"""
    __tablename__ = "scenario_results"

    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"), nullable=False)
    simulation_run_date = Column(DateTime, default=datetime.utcnow)
    total_estate_value = Column(Numeric(15, 2))
    federal_estate_tax = Column(Numeric(15, 2))
    state_estate_tax = Column(Numeric(15, 2))
    total_taxes = Column(Numeric(15, 2))
    net_to_family = Column(Numeric(15, 2))
    charitable_distribution = Column(Numeric(15, 2), default=0)
    spouse_distribution = Column(Numeric(15, 2), default=0)
    children_distribution = Column(Numeric(15, 2), default=0)
    other_distribution = Column(Numeric(15, 2), default=0)
    breakdown_by_beneficiary = Column(JSON)  # Detailed breakdown
    assumptions_snapshot = Column(JSON)  # Tax rates and assumptions used

    scenario = relationship("Scenario", back_populates="results")


class TimelineEvent(Base):
    """Estate plan timeline events"""
    __tablename__ = "timeline_events"

    id = Column(Integer, primary_key=True)
    estate_plan_id = Column(Integer, ForeignKey("estate_plans.id"))
    event_type = Column(String(100))  # "death", "distribution", "review", "tax_event"
    event_date = Column(Date, nullable=False)
    event_title = Column(String(255), nullable=False)
    event_description = Column(Text)
    affected_parties = Column(JSON)  # List of family members affected
    tax_impact = Column(Numeric(15, 2))


# ============================================================================
# DOCUMENTS & PRESENTATIONS
# ============================================================================

class Document(Base):
    """Uploaded estate planning documents"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    estate_id = Column(Integer, ForeignKey("estates.id"), nullable=False)
    document_type = Column(String(50))  # "will", "trust", "deed", "insurance", etc.
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # Cloud storage path
    upload_date = Column(DateTime, default=datetime.utcnow)
    summary = Column(Text)  # AI-generated summary
    key_provisions = Column(JSON)  # Extracted key points
    extracted_text = Column(Text)  # OCR/extracted text
    notes = Column(Text)

    estate = relationship("Estate", back_populates="documents")


class Presentation(Base):
    """Generated presentations and reports"""
    __tablename__ = "presentations"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    estate_id = Column(Integer, ForeignKey("estates.id"))
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    presentation_type = Column(String(50))  # "pdf", "pptx", "html"
    presentation_name = Column(String(255), nullable=False)
    file_path = Column(String(500))  # Cloud storage path
    generated_date = Column(DateTime, default=datetime.utcnow)
    white_label_org = Column(String(255))  # For white-label presentations
    template_used = Column(String(100))
    includes_tax_summary = Column(Boolean, default=True)
    includes_family_tree = Column(Boolean, default=True)
    includes_timeline = Column(Boolean, default=False)
    includes_scenario_comparison = Column(Boolean, default=False)

    client = relationship("Client", back_populates="presentations")
    estate = relationship("Estate", foreign_keys=[estate_id])
    scenario = relationship("Scenario", foreign_keys=[scenario_id])
