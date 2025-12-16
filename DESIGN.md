# Financial Planning Application - Design Document

## Overview

A comprehensive estate planning and financial analysis platform that enables advisors and families to:
- Model and visualize estate plans
- Calculate complex federal and state estate taxes
- Simulate various planning scenarios
- Track exemptions, insurance, and assets
- Generate professional presentations and family timelines

## Technology Stack

### Backend/Analytics
- **Python 3.11+** - Core analytics and calculation engine
- **FastAPI** - REST API framework for real-time calculations
- **SQLAlchemy** - ORM for database operations
- **Pydantic** - Data validation and serialization
- **numpy/pandas** - Numerical and statistical computations
- **OpenAI/Claude API** - AI document summarization

### Frontend
- **React 18+** - UI framework
- **D3.js / Plotly** - Charting and visualization
- **TailwindCSS** - Styling
- **React Flow** - Diagram/flowchart rendering

### Database
- **PostgreSQL** - Primary relational database
- **Redis** - Caching and session management

### Documentation/Reporting
- **Jinja2** - Template rendering
- **Reportlab/WeasyPrint** - PDF generation
- **python-pptx** - Presentation generation

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend Layer                               │
│              (React, D3.js, React Flow)                          │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│                    API Layer (FastAPI)                           │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │   Estate     │ │   Family     │ │   Simulation │             │
│  │  Routes      │ │  Routes      │ │  Routes      │             │
│  └──────────────┘ └──────────────┘ └──────────────┘             │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│              Analytics Layer (Python)                            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │ Tax Engine   │ │ Simulation   │ │ Exemption    │             │
│  │              │ │ Engine       │ │ Tracker      │             │
│  └──────────────┘ └──────────────┘ └──────────────┘             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │ Document     │ │ Presentation │ │ Calculation  │             │
│  │ Analyzer     │ │ Generator    │ │ Services     │             │
│  └──────────────┘ └──────────────┘ └──────────────┘             │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│              Data Models & Database                              │
│         (SQLAlchemy + PostgreSQL)                               │
└─────────────────────────────────────────────────────────────────┘
```

## Core Data Models

### 1. Estate/Client Management
- **Client** - Individual/couple entity
- **Estate** - Client's estate information
- **FamilyMember** - Beneficiaries and family structure
- **FamilyTree** - Hierarchical family relationships

### 2. Asset Management
- **Asset** - Real estate, investments, business interests, etc.
- **AssetAllocation** - How assets pass to beneficiaries
- **LifeInsurancePolicy** - Insurance holdings
- **PromissoryNote** - Loans and notes

### 3. Tax & Exemption Tracking
- **TaxRate** - Federal/state estate tax rates by year
- **GiftExemption** - Lifetime gift tax exemption tracking
- **GSTExemption** - Generation-skipping transfer exemption
- **EstateTransaction** - Individual exemption usage

### 4. Plans & Scenarios
- **EstatePlan** - Primary estate plan document
- **Scenario** - Simulation variants
- **TimelineEvent** - Estate plan timeline events

### 5. Integration/Documents
- **Document** - Uploaded documents for AI summarization
- **Presentation** - Generated reports/presentations

## Module Structure

```
financial-planning-app/
├── backend/
│   ├── analytics/
│   │   ├── tax_engine.py
│   │   ├── simulation_engine.py
│   │   ├── exemption_tracker.py
│   │   ├── calculations/
│   │   │   ├── federal_estate_tax.py
│   │   │   ├── state_estate_tax.py
│   │   │   ├── income_tax.py
│   │   │   └── gst_calculations.py
│   │   └── models/
│   │       ├── estate_models.py
│   │       ├── asset_models.py
│   │       └── tax_models.py
│   │
│   ├── services/
│   │   ├── document_analyzer.py
│   │   ├── presentation_generator.py
│   │   ├── diagram_generator.py
│   │   ├── timeline_generator.py
│   │   └── family_tree_service.py
│   │
│   ├── database/
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── repositories/
│   │   │   ├── estate_repo.py
│   │   │   ├── asset_repo.py
│   │   │   └── tax_repo.py
│   │   └── migrations/
│   │
│   ├── api/
│   │   ├── main.py
│   │   ├── routes/
│   │   │   ├── estates.py
│   │   │   ├── families.py
│   │   │   ├── assets.py
│   │   │   ├── simulations.py
│   │   │   ├── scenarios.py
│   │   │   ├── taxes.py
│   │   │   ├── presentations.py
│   │   │   └── documents.py
│   │   └── middleware/
│   │
│   └── config/
│       ├── settings.py
│       └── database.py
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── utils/
│   └── package.json
│
├── requirements.txt
├── docker-compose.yml
└── DESIGN.md
```

## Key Features Design

### 1. Estate Tax Calculation Engine
- Calculate federal estate tax based on:
  - Taxable estate value
  - Marital deduction
  - Annual exclusion gifts
  - Lifetime exemption usage
- State-specific estate/inheritance tax calculations
- Multi-state property considerations
- Step-up in basis calculations

### 2. Simulation & Scenario Modeling
- Create variants of estate plans with different:
  - Asset values (appreciation/depreciation)
  - Life expectancies
  - Market conditions
  - Tax law changes
  - Gifting strategies
- Compare outcomes across scenarios
- Monte Carlo simulations for uncertainty modeling

### 3. Exemption Tracking System
- Track lifetime gift tax exemption usage per beneficiary
- Monitor GST exemption allocations
- Track annual exclusion gifts ($18,000 indexed annually)
- Portability election tracking for married couples
- Historical exemption usage records

### 4. Document Analysis (AI)
- Upload estate planning documents (wills, trusts, etc.)
- AI summarization of key provisions
- Extraction of:
  - Executor/trustee information
  - Beneficiary distribution instructions
  - Tax clause details
  - Special provisions

### 5. Presentation Generation
- White-label customizable presentations
- PDF reports with:
  - Estate analysis summaries
  - Tax projections
  - Asset allocation charts
  - Scenario comparison tables
- PowerPoint/Keynote deck generation

### 6. Visualization & Diagrams
- Estate plan flow diagrams showing:
  - Asset flow to beneficiaries
  - Trust structures
  - Conditional distributions
- Family tree visualization
- Asset allocation pie charts
- Tax projection line charts
- Timeline visualization

### 7. Family Timeline Management
- Create milestone events:
  - Birth/death dates
  - Distribution dates
  - Review dates
  - Tax event dates
- Timeline visualization
- Dependency tracking between events

## Database Schema Highlights

### Key Tables
```sql
-- Core entities
CREATE TABLE clients (id, name, email, created_at);
CREATE TABLE estates (id, client_id, date_created, assets_total);
CREATE TABLE family_members (id, estate_id, name, relationship, dob, dod);
CREATE TABLE assets (id, estate_id, description, value, type, date_acquired);
CREATE TABLE life_insurance_policies (id, estate_id, policy_number, face_value, premium, owner);

-- Tax tracking
CREATE TABLE tax_rates (id, year, jurisdiction, estate_tax_rate, gift_tax_rate);
CREATE TABLE gift_exemptions (id, client_id, year, amount_used, amount_available);
CREATE TABLE gst_exemptions (id, beneficiary_id, amount_allocated, date_allocated);

-- Planning
CREATE TABLE estate_plans (id, estate_id, created_date, assets_distribution);
CREATE TABLE scenarios (id, estate_plan_id, name, description, created_date);
CREATE TABLE scenario_variables (id, scenario_id, variable_name, value);
CREATE TABLE scenario_results (id, scenario_id, estate_tax, net_to_family);

-- Documents & Presentations
CREATE TABLE documents (id, estate_id, file_path, upload_date, summary);
CREATE TABLE presentations (id, estate_id, scenario_id, format, generated_date);
```

## API Endpoint Structure

### Estate Management
```
GET/POST   /api/estates
GET/PUT    /api/estates/{id}
GET        /api/estates/{id}/summary
GET        /api/estates/{id}/analysis
```

### Family
```
GET/POST   /api/estates/{id}/family-members
GET        /api/estates/{id}/family-tree
PUT        /api/family-members/{id}
DELETE     /api/family-members/{id}
```

### Assets & Insurance
```
GET/POST   /api/estates/{id}/assets
PUT        /api/assets/{id}
DELETE     /api/assets/{id}
GET/POST   /api/estates/{id}/insurance-policies
```

### Tax Calculations
```
POST       /api/estates/{id}/calculate-taxes
GET        /api/estates/{id}/tax-summary
POST       /api/tax-rates/update
GET        /api/tax-rates/{jurisdiction}/{year}
```

### Scenarios & Simulations
```
POST       /api/estates/{id}/scenarios
GET        /api/scenarios/{id}
POST       /api/scenarios/{id}/run-simulation
GET        /api/scenarios/{id}/results
POST       /api/scenarios/{id}/compare
```

### Exemption Tracking
```
GET        /api/estates/{id}/exemption-status
POST       /api/estates/{id}/gift-transactions
GET        /api/estates/{id}/gst-allocations
PUT        /api/estates/{id}/gst-allocations/{id}
```

### Presentations & Reports
```
POST       /api/estates/{id}/generate-presentation
POST       /api/estates/{id}/generate-diagram
POST       /api/estates/{id}/generate-timeline
GET        /api/presentations/{id}/download
```

### Document Analysis
```
POST       /api/estates/{id}/documents/upload
POST       /api/documents/{id}/summarize
GET        /api/documents/{id}/summary
```

## Key Calculation Formulas

### Federal Estate Tax (2024)
```
Taxable Estate = Gross Estate
                - Administration Expenses
                - Marital Deduction
                - Charitable Deduction
                - Annual Exclusion Gifts

Estate Tax = Max(0, (Taxable Estate - Exemption) * Tax Rate)

Exemption (2024) = $13.61M (indexed annually)
```

### State Estate Tax (varies by state)
- Connecticut, Illinois, Maine, Maryland, Massachusetts, Minnesota, New York, Oregon, Rhode Island, Vermont, Washington
- Different thresholds and rates per state

### Gift/GST Exemption Tracking
```
Available Exemption = Lifetime Exemption - Used Exemption
Taxable Gift = Max(0, Gift Amount - Annual Exclusion - Available Exemption)
```

## Integration Points

1. **AI Integration** - Document summarization and analysis
2. **PDF Generation** - Reports and presentations
3. **Financial Data APIs** - Asset valuation (optional)
4. **Email Service** - Presentation delivery
5. **Cloud Storage** - Document and presentation storage

## Security Considerations

1. End-to-end encryption for sensitive documents
2. Role-based access control (RBAC)
3. Audit logging for all calculations and changes
4. Compliance with financial data regulations (PCI, HIPAA considerations)
5. Secure API authentication (OAuth 2.0)
6. Data retention policies

## Scalability & Performance

1. Caching frequently accessed tax rates
2. Asynchronous task processing for simulations
3. Database indexing on frequently queried fields
4. Pagination for large datasets
5. GraphQL for efficient data queries (optional upgrade)

## Phase Implementation

### Phase 1: Core Foundation
- Data models and database
- Basic estate and family management
- Asset tracking

### Phase 2: Analytics
- Tax calculation engine
- Federal/state estate tax calculations
- Exemption tracking

### Phase 3: Scenario Planning
- Simulation engine
- Variable-based scenarios
- Comparison tools

### Phase 4: Visualization & Reporting
- Diagram generation
- Presentation generator
- Timeline creation

### Phase 5: Advanced Features
- AI document analysis
- White-label customization
- Insurance integration
- Promissory note tracking with amortization

### Phase 6: Optimization
- Performance optimization
- Advanced UI/UX
- Third-party integrations
