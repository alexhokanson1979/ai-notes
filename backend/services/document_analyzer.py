"""
Document Analysis Service

Analyzes estate planning documents using AI:
- Summarizes wills, trusts, and other legal documents
- Extracts key provisions and data
- Identifies potential issues
- Suggests recommendations
"""

from typing import Dict, List, Optional
import json


class DocumentAnalyzer:
    """Analyze estate planning documents"""

    def __init__(self, ai_service=None):
        """
        Initialize analyzer with optional AI service (OpenAI/Claude).

        Args:
            ai_service: AI service for document analysis (optional)
        """
        self.ai_service = ai_service

    def analyze_document(
        self,
        document_text: str,
        document_type: str,  # "will", "trust", "deed", etc.
    ) -> Dict:
        """
        Analyze an estate planning document.

        Args:
            document_text: Full text of document
            document_type: Type of document

        Returns:
            Analysis results including summary and extracted data
        """

        analysis = {
            "document_type": document_type,
            "summary": self._extract_summary(document_text, document_type),
            "key_provisions": self._extract_key_provisions(document_text, document_type),
            "beneficiaries": self._extract_beneficiaries(document_text),
            "executors_trustees": self._extract_fiduciaries(document_text),
            "tax_provisions": self._extract_tax_provisions(document_text),
            "special_provisions": self._extract_special_provisions(document_text),
            "potential_issues": self._identify_issues(document_text, document_type),
            "recommendations": self._generate_recommendations(document_text, document_type),
        }

        return analysis

    def summarize_document(self, document_text: str) -> str:
        """
        Generate AI-powered summary of document.

        Args:
            document_text: Document text to summarize

        Returns:
            AI-generated summary
        """

        if self.ai_service:
            # Use AI service for intelligent summarization
            summary = self.ai_service.summarize(
                text=document_text,
                max_length=500,
            )
            return summary
        else:
            # Fallback to simple extraction
            return self._extract_summary(document_text, "document")

    def extract_beneficiary_list(self, document_text: str) -> List[Dict]:
        """
        Extract all beneficiaries mentioned in document.

        Args:
            document_text: Document text

        Returns:
            List of beneficiaries with details
        """

        beneficiaries = []
        beneficiary_keywords = [
            "beneficiary", "heir", "legatee", "devisee", "recipient",
            "shall receive", "is devised to", "shall pass to"
        ]

        # Simple pattern matching (would be more sophisticated with NLP)
        lines = document_text.split('\n')

        for line in lines:
            for keyword in beneficiary_keywords:
                if keyword.lower() in line.lower():
                    # Extract names and amounts from this section
                    beneficiary_info = self._parse_beneficiary_clause(line)
                    if beneficiary_info:
                        beneficiaries.append(beneficiary_info)

        return beneficiaries

    def extract_asset_distributions(self, document_text: str) -> List[Dict]:
        """
        Extract asset distributions from document.

        Args:
            document_text: Document text

        Returns:
            List of asset distributions
        """

        distributions = []
        asset_keywords = [
            "devise", "bequest", "legacy", "distribute",
            "pass to", "transferred to", "left to"
        ]

        lines = document_text.split('\n')

        for line in lines:
            for keyword in asset_keywords:
                if keyword.lower() in line.lower():
                    # Extract asset and recipient
                    distrib = self._parse_distribution_clause(line)
                    if distrib:
                        distributions.append(distrib)

        return distributions

    def extract_tax_clauses(self, document_text: str) -> Dict:
        """
        Extract tax-related clauses from document.

        Args:
            document_text: Document text

        Returns:
            Tax clause information
        """

        clauses = {
            "tax_apportionment": None,
            "tax_payment_clause": None,
            "marital_deduction_clause": None,
            "charitable_deduction_clause": None,
            "gst_exemption_allocations": None,
            "power_of_appointment": None,
            "other_tax_provisions": [],
        }

        tax_keywords = [
            "tax", "estate tax", "income tax", "death tax",
            "apportionment", "marital deduction", "charitable",
            "GST", "generation-skipping"
        ]

        lines = document_text.split('\n')

        for i, line in enumerate(lines):
            for keyword in tax_keywords:
                if keyword.lower() in line.lower():
                    # Extract context around tax-related clause
                    context = '\n'.join(lines[max(0, i-2):min(len(lines), i+3)])
                    clauses["other_tax_provisions"].append(context)

        return clauses

    def check_consistency(self, documents: List[str]) -> Dict:
        """
        Check consistency across multiple documents (will, trust, etc.).

        Args:
            documents: List of document texts

        Returns:
            Consistency check results
        """

        inconsistencies = []

        # Extract beneficiaries from each document
        beneficiary_lists = [
            self.extract_beneficiary_list(doc) for doc in documents
        ]

        # Check if beneficiary lists match
        for i in range(len(beneficiary_lists) - 1):
            if set(beneficiary_lists[i]) != set(beneficiary_lists[i + 1]):
                inconsistencies.append({
                    "type": "beneficiary_mismatch",
                    "severity": "High",
                    "description": "Beneficiary lists differ across documents",
                })

        return {
            "documents_checked": len(documents),
            "inconsistencies_found": len(inconsistencies),
            "issues": inconsistencies,
        }

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    @staticmethod
    def _extract_summary(document_text: str, document_type: str) -> str:
        """Extract or generate summary of document"""

        summaries = {
            "will": "Last will and testament providing instructions for property distribution and appointment of fiduciaries",
            "trust": "Trust document outlining trustee powers and beneficiary distributions",
            "deed": "Property deed showing ownership transfer or titling",
            "insurance": "Insurance policy document showing coverage and beneficiaries",
            "power_of_attorney": "Power of attorney granting agent authority to act on behalf of principal",
        }

        # Get template summary
        summary = summaries.get(document_type, "Estate planning document")

        # Attempt to extract first meaningful section
        lines = document_text.split('\n')
        for line in lines:
            if len(line) > 20 and not line.startswith(' '):
                summary = line.strip()[:200]
                break

        return summary

    @staticmethod
    def _extract_key_provisions(document_text: str, document_type: str) -> List[str]:
        """Extract key provisions from document"""

        provisions = []
        key_phrases = [
            "hereby declare", "give, devise and bequeath",
            "upon the death of", "in the event of death",
            "the trustee shall", "I appoint", "I nominate"
        ]

        for phrase in key_phrases:
            if phrase.lower() in document_text.lower():
                provisions.append(f"Contains clause: {phrase}")

        return provisions

    @staticmethod
    def _extract_beneficiaries(document_text: str) -> List[Dict]:
        """Extract beneficiary information"""

        beneficiaries = []
        beneficiary_patterns = ["my son", "my daughter", "my spouse", "my child"]

        for pattern in beneficiary_patterns:
            if pattern.lower() in document_text.lower():
                beneficiaries.append({
                    "relationship": pattern,
                    "mentioned": True,
                })

        return beneficiaries

    @staticmethod
    def _extract_fiduciaries(document_text: str) -> List[Dict]:
        """Extract executor/trustee information"""

        fiduciaries = []
        fiduciary_titles = ["executor", "trustee", "administrator", "guardian"]

        for title in fiduciary_titles:
            if title.lower() in document_text.lower():
                fiduciaries.append({
                    "role": title,
                    "mentioned": True,
                })

        return fiduciaries

    @staticmethod
    def _extract_tax_provisions(document_text: str) -> Dict:
        """Extract tax-related provisions"""

        provisions = {
            "has_tax_apportionment_clause": "apportionment" in document_text.lower(),
            "has_marital_deduction_language": "marital" in document_text.lower(),
            "has_charitable_language": "charitable" in document_text.lower(),
            "addresses_estate_tax": "estate tax" in document_text.lower(),
        }

        return provisions

    @staticmethod
    def _extract_special_provisions(document_text: str) -> List[str]:
        """Extract special provisions (conditions, powers, etc.)"""

        provisions = []
        special_keywords = [
            "condition", "contingency", "power of appointment",
            "spendthrift", "discretionary", "remainder", "perpetuity"
        ]

        for keyword in special_keywords:
            if keyword.lower() in document_text.lower():
                provisions.append(f"Contains provision: {keyword}")

        return provisions

    @staticmethod
    def _identify_issues(document_text: str, document_type: str) -> List[Dict]:
        """Identify potential issues in document"""

        issues = []

        # Check for outdated language
        if "shall vest and be in full force" in document_text:
            issues.append({
                "type": "outdated_language",
                "severity": "Low",
                "description": "Document may contain outdated legal language",
                "recommendation": "Consider updating with modern language",
            })

        # Check for missing provisions
        if document_type == "will" and "guardian" not in document_text.lower():
            issues.append({
                "type": "missing_guardianship",
                "severity": "High",
                "description": "No guardian appointment for minor children",
                "recommendation": "Add guardian provision if children are minors",
            })

        # Check for potential tax issues
        if "marital" not in document_text.lower() and "spouse" in document_text.lower():
            issues.append({
                "type": "missing_marital_deduction",
                "severity": "Medium",
                "description": "No apparent marital deduction planning",
                "recommendation": "Consider marital deduction provisions if spouse inheriting substantial assets",
            })

        return issues

    @staticmethod
    def _generate_recommendations(document_text: str, document_type: str) -> List[str]:
        """Generate recommendations for document updates"""

        recommendations = []

        # General recommendations
        recommendations.append("Review document with tax advisor to optimize estate tax planning")
        recommendations.append("Ensure beneficiary designations align with this document")

        # Specific recommendations
        if document_type == "will":
            recommendations.append("Consider whether revocable living trust would be appropriate")
            recommendations.append("Review executor's powers and compensation")

        elif document_type == "trust":
            recommendations.append("Review trustee succession provisions")
            recommendations.append("Consider adding protector role for added flexibility")

        recommendations.append("Update document every 3-5 years or when significant life changes occur")

        return recommendations

    @staticmethod
    def _parse_beneficiary_clause(line: str) -> Optional[Dict]:
        """Parse beneficiary from a clause"""

        # Simplified parsing - would be more sophisticated with NLP
        if any(name in line for name in ["John", "Jane", "Mary", "James", "Michael"]):
            return {
                "name": "Extracted Name",
                "allocation": "To be determined",
                "conditions": None,
            }

        return None

    @staticmethod
    def _parse_distribution_clause(line: str) -> Optional[Dict]:
        """Parse distribution from a clause"""

        # Simplified parsing
        return {
            "asset_description": "Extracted from clause",
            "recipient": "To be determined",
            "allocation": "Per document",
        }
