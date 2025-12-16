"""
Financial Planning Application Backend Package
"""

__version__ = "1.0.0"
__author__ = "Financial Planning Development Team"

from .analytics.calculations.federal_estate_tax import FederalEstateTaxCalculator
from .analytics.calculations.state_estate_tax import StateEstateTaxCalculator
from .analytics.calculations.gst_calculations import GSTExemptionTracker
from .analytics.simulation_engine import EstateSimulationEngine
from .services.presentation_generator import PresentationGenerator
from .services.document_analyzer import DocumentAnalyzer
from .services.family_tree_service import FamilyTreeService

__all__ = [
    "FederalEstateTaxCalculator",
    "StateEstateTaxCalculator",
    "GSTExemptionTracker",
    "EstateSimulationEngine",
    "PresentationGenerator",
    "DocumentAnalyzer",
    "FamilyTreeService",
]
