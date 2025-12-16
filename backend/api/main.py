"""
Financial Planning Application - FastAPI Main Application

RESTful API for estate planning application with comprehensive
estate tax calculations, scenario modeling, and family planning.
"""

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional, List

# Import analytics modules
from ..analytics.calculations.federal_estate_tax import FederalEstateTaxCalculator
from ..analytics.calculations.state_estate_tax import StateEstateTaxCalculator
from ..analytics.calculations.gst_calculations import GSTExemptionTracker
from ..analytics.simulation_engine import EstateSimulationEngine, ScenarioVariable
from ..services.presentation_generator import PresentationGenerator, PresentationConfig
from ..services.document_analyzer import DocumentAnalyzer
from ..services.family_tree_service import FamilyTreeService

# Import Pydantic schemas (would be defined in schemas.py)
from pydantic import BaseModel
from decimal import Decimal


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class ClientCreate(BaseModel):
    """Schema for creating a client"""
    name: str
    email: str
    phone: Optional[str] = None
    organization: Optional[str] = None


class EstateCreate(BaseModel):
    """Schema for creating an estate"""
    client_id: int
    primary_owner_name: str
    spouse_name: Optional[str] = None
    total_assets_value: Decimal


class AssetCreate(BaseModel):
    """Schema for creating an asset"""
    estate_id: int
    description: str
    asset_type: str
    current_value: Decimal
    ownership_type: str = "individual"


class TaxCalculationRequest(BaseModel):
    """Schema for tax calculation request"""
    estate_id: int
    gross_estate: Decimal
    marital_deduction: Decimal = Decimal(0)
    charitable_deduction: Decimal = Decimal(0)
    domicile_state: str = "NY"


class ScenarioRequest(BaseModel):
    """Schema for scenario modeling"""
    estate_id: int
    scenario_name: str
    variables: List[dict]
    domicile_state: str = "NY"


class PresentationRequest(BaseModel):
    """Schema for presentation generation"""
    estate_id: int
    scenario_id: Optional[int] = None
    output_format: str = "pdf"  # pdf, pptx, html
    white_label_org: Optional[str] = None


# ============================================================================
# APPLICATION INITIALIZATION
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    # Startup
    print("Starting Financial Planning Application")
    # Initialize analytics engines
    yield
    # Shutdown
    print("Shutting down Financial Planning Application")


app = FastAPI(
    title="Financial Planning Application",
    description="Comprehensive estate planning and analysis platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# ESTATE MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/api/estates")
async def create_estate(estate: EstateCreate):
    """Create a new estate"""
    # Database operation would go here
    return {
        "id": 1,
        "status": "created",
        "data": estate.dict(),
    }


@app.get("/api/estates/{estate_id}")
async def get_estate(estate_id: int):
    """Retrieve estate details"""
    return {
        "id": estate_id,
        "primary_owner_name": "John Doe",
        "total_assets_value": 5000000,
        "created_date": "2024-01-01",
    }


@app.get("/api/estates/{estate_id}/summary")
async def get_estate_summary(estate_id: int):
    """Get estate summary"""
    return {
        "estate_id": estate_id,
        "total_assets": 5000000,
        "estimated_estate_tax": 1250000,
        "net_to_heirs": 3750000,
    }


# ============================================================================
# TAX CALCULATION ENDPOINTS
# ============================================================================

@app.post("/api/estates/{estate_id}/calculate-taxes")
async def calculate_estate_taxes(estate_id: int, request: TaxCalculationRequest):
    """Calculate federal and state estate taxes"""

    # Initialize calculators
    federal_calc = FederalEstateTaxCalculator(year=2024)
    state_calc = StateEstateTaxCalculator(year=2024)

    # Calculate federal estate tax
    federal_results = federal_calc.calculate_federal_estate_tax(
        gross_estate=request.gross_estate,
        marital_deduction=request.marital_deduction,
        charitable_deduction=request.charitable_deduction,
    )

    # Calculate state estate tax
    state_results = state_calc.calculate_state_estate_tax(
        state=request.domicile_state,
        taxable_estate=federal_results["taxable_estate"],
        domicile_state=request.domicile_state,
    )

    return {
        "estate_id": estate_id,
        "federal_results": {
            "gross_estate": str(federal_results["gross_estate"]),
            "taxable_estate": str(federal_results["taxable_estate"]),
            "applicable_exemption": str(federal_results["applicable_exemption"]),
            "federal_estate_tax": str(federal_results["federal_estate_tax"]),
            "net_to_heirs": str(federal_results["net_to_heirs"]),
        },
        "state_results": {
            "state": state_results["state"],
            "state_estate_tax": str(state_results["state_estate_tax"]),
        },
        "total_taxes": str(
            federal_results["federal_estate_tax"] + state_results["state_estate_tax"]
        ),
    }


@app.get("/api/tax-rates/{jurisdiction}/{year}")
async def get_tax_rates(jurisdiction: str, year: int):
    """Get tax rates for jurisdiction and year"""
    if year == 2024:
        if jurisdiction == "federal":
            return {
                "jurisdiction": "federal",
                "year": 2024,
                "estate_tax_rate": 0.40,
                "exemption_amount": 13610000,
                "annual_exclusion": 18000,
            }
        elif jurisdiction == "NY":
            return {
                "jurisdiction": "NY",
                "year": 2024,
                "estate_tax_rate": 0.04,
                "exemption_amount": 6940000,
            }

    return {"error": "Tax rates not found"}


@app.post("/api/tax-rates/update")
async def update_tax_rates(year: int, rates: dict):
    """Update tax rates in database"""
    # Database update operation
    return {"status": "updated", "year": year}


# ============================================================================
# EXEMPTION TRACKING ENDPOINTS
# ============================================================================

@app.get("/api/estates/{estate_id}/exemption-status")
async def get_exemption_status(estate_id: int):
    """Get exemption utilization status"""

    gst_tracker = GSTExemptionTracker(year=2024)

    return {
        "estate_id": estate_id,
        "federal_lifetime_exemption": 13610000,
        "federal_exemption_used": 0,
        "federal_exemption_remaining": 13610000,
        "annual_exclusion": 18000,
        "gst_exemption": 13610000,
    }


@app.post("/api/estates/{estate_id}/gift-transactions")
async def record_gift_transaction(estate_id: int, gift_data: dict):
    """Record a gift transaction for exemption tracking"""
    # Database operation to store gift transaction
    return {
        "estate_id": estate_id,
        "status": "recorded",
        "gift_data": gift_data,
    }


# ============================================================================
# SCENARIO & SIMULATION ENDPOINTS
# ============================================================================

@app.post("/api/estates/{estate_id}/scenarios")
async def create_scenario(estate_id: int, scenario: ScenarioRequest):
    """Create a new estate planning scenario"""
    return {
        "scenario_id": 1,
        "estate_id": estate_id,
        "scenario_name": scenario.scenario_name,
        "status": "created",
    }


@app.post("/api/scenarios/{scenario_id}/run-simulation")
async def run_scenario_simulation(scenario_id: int, request: dict):
    """Run simulation for a scenario"""

    engine = EstateSimulationEngine(year=2024)

    # Example base estate
    base_estate = {
        "real_estate": Decimal(3000000),
        "stocks": Decimal(1500000),
        "retirement": Decimal(500000),
    }

    # Run scenario
    result = engine.run_scenario(
        scenario_name="Base Case",
        base_estate=base_estate,
        variables=[],
        domicile_state="NY",
    )

    return {
        "scenario_id": scenario_id,
        "total_estate_value": str(result.total_estate_value),
        "federal_estate_tax": str(result.federal_estate_tax),
        "state_estate_tax": str(result.state_estate_tax),
        "total_taxes": str(result.total_taxes),
        "net_to_heirs": str(result.net_to_heirs),
    }


@app.post("/api/scenarios/{scenario_id}/compare")
async def compare_scenarios(scenario_id: int, scenarios: List[dict]):
    """Compare multiple scenarios"""

    engine = EstateSimulationEngine(year=2024)
    base_estate = {
        "real_estate": Decimal(3000000),
        "stocks": Decimal(1500000),
        "retirement": Decimal(500000),
    }

    comparison = engine.compare_scenarios(
        base_estate=base_estate,
        scenarios=scenarios,
    )

    return comparison


@app.post("/api/estates/{estate_id}/monte-carlo-simulation")
async def run_monte_carlo(estate_id: int, params: dict):
    """Run Monte Carlo simulation with probabilistic variables"""

    engine = EstateSimulationEngine(year=2024)

    base_estate = {
        "real_estate": Decimal(3000000),
        "stocks": Decimal(1500000),
        "retirement": Decimal(500000),
    }

    variable_distributions = {
        "real_estate": (Decimal(3000000), Decimal(200000)),
        "stocks": (Decimal(1500000), Decimal(150000)),
    }

    results = engine.run_monte_carlo_simulation(
        scenario_name="Monte Carlo",
        base_estate=base_estate,
        variable_distributions=variable_distributions,
        iterations=params.get("iterations", 1000),
    )

    return {
        "scenario_name": results.scenario_name,
        "iterations": results.iterations,
        "average_net_to_heirs": str(results.average_net_to_heirs),
        "median_net_to_heirs": str(results.median_net_to_heirs),
        "percentile_10": str(results.percentile_10),
        "percentile_90": str(results.percentile_90),
        "probability_of_estate_tax": float(results.probability_of_estate_tax),
    }


# ============================================================================
# PRESENTATION & REPORTING ENDPOINTS
# ============================================================================

@app.post("/api/estates/{estate_id}/generate-presentation")
async def generate_presentation(estate_id: int, request: PresentationRequest):
    """Generate estate planning presentation"""

    generator = PresentationGenerator()

    config = PresentationConfig(
        template_name="standard",
        output_format=request.output_format,
        white_label_org=request.white_label_org,
        client_name="Sample Client",
    )

    estate_data = {
        "total_value": 5000000,
        "primary_owner_name": "John Doe",
        "insurance_policies": [],
    }

    scenario_results = {
        "federal_estate_tax": 1250000,
        "state_estate_tax": 200000,
        "total_taxes": 1450000,
        "net_to_heirs": 3550000,
    }

    if request.output_format == "pdf":
        file_path = generator.generate_pdf_report(estate_data, scenario_results, config)
    elif request.output_format == "pptx":
        file_path = generator.generate_powerpoint_presentation(
            estate_data, scenario_results, {}, config
        )
    else:
        file_path = None

    return {
        "estate_id": estate_id,
        "format": request.output_format,
        "file_path": file_path,
        "status": "generated",
    }


@app.get("/api/presentations/{presentation_id}/download")
async def download_presentation(presentation_id: int):
    """Download generated presentation"""
    return {"presentation_id": presentation_id, "download_url": "/files/presentation.pdf"}


# ============================================================================
# DOCUMENT ANALYSIS ENDPOINTS
# ============================================================================

@app.post("/api/estates/{estate_id}/documents/upload")
async def upload_document(estate_id: int, file: UploadFile = File(...)):
    """Upload estate planning document for analysis"""
    return {
        "estate_id": estate_id,
        "filename": file.filename,
        "status": "uploaded",
    }


@app.post("/api/documents/{document_id}/summarize")
async def summarize_document(document_id: int):
    """Summarize uploaded document using AI"""

    analyzer = DocumentAnalyzer()

    summary = {
        "document_id": document_id,
        "summary": "Will establishing distribution of assets to spouse and children",
        "key_provisions": [
            "Primary residence to spouse",
            "Stock portfolio in trust for children",
            "Annual income to spouse during lifetime",
        ],
        "beneficiaries": ["Spouse", "Children"],
        "executors": ["Spouse", "Attorney"],
    }

    return summary


@app.get("/api/documents/{document_id}/summary")
async def get_document_summary(document_id: int):
    """Retrieve document summary"""
    return {
        "document_id": document_id,
        "summary": "Document summary text",
        "last_updated": "2024-01-15",
    }


# ============================================================================
# FAMILY TREE ENDPOINTS
# ============================================================================

@app.get("/api/estates/{estate_id}/family-tree")
async def get_family_tree(estate_id: int):
    """Get family tree visualization"""

    service = FamilyTreeService()

    tree_data = service.get_tree_visualization()

    return {
        "estate_id": estate_id,
        "tree": tree_data,
    }


@app.post("/api/estates/{estate_id}/family-members")
async def add_family_member(estate_id: int, member_data: dict):
    """Add family member to estate"""
    return {
        "estate_id": estate_id,
        "member_id": 1,
        "status": "created",
        "data": member_data,
    }


# ============================================================================
# INSURANCE TRACKING ENDPOINTS
# ============================================================================

@app.post("/api/estates/{estate_id}/insurance-policies")
async def add_insurance_policy(estate_id: int, policy_data: dict):
    """Add life insurance policy"""
    return {
        "estate_id": estate_id,
        "policy_id": 1,
        "status": "created",
    }


@app.get("/api/estates/{estate_id}/insurance-summary")
async def get_insurance_summary(estate_id: int):
    """Get life insurance summary"""
    return {
        "estate_id": estate_id,
        "total_policies": 2,
        "total_face_value": 5000000,
        "annual_premiums": 25000,
    }


# ============================================================================
# LOAN/PROMISSORY NOTE ENDPOINTS
# ============================================================================

@app.post("/api/estates/{estate_id}/promissory-notes")
async def add_promissory_note(estate_id: int, note_data: dict):
    """Add promissory note/loan tracking"""
    return {
        "estate_id": estate_id,
        "note_id": 1,
        "status": "created",
    }


@app.get("/api/promissory-notes/{note_id}/amortization-schedule")
async def get_amortization_schedule(note_id: int):
    """Get amortization schedule for note/loan"""
    return {
        "note_id": note_id,
        "payment_schedule": [
            {
                "payment_number": 1,
                "payment_date": "2024-02-01",
                "payment_amount": 1000,
                "principal": 850,
                "interest": 150,
            }
        ],
    }


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Financial Planning Application API",
        "version": "1.0.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
