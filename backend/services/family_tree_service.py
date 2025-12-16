"""
Family Tree Service

Generates and manages family tree visualizations and relationships.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import date


@dataclass
class FamilyMemberNode:
    """Represents a family member in the tree"""
    member_id: int
    name: str
    generation_level: int
    relationship: str
    date_of_birth: Optional[date] = None
    date_of_death: Optional[date] = None
    is_alive: bool = True
    assets_to_inherit: float = 0.0


class FamilyTreeService:
    """Generate and manage family tree data"""

    def __init__(self):
        self.members: Dict[int, FamilyMemberNode] = {}
        self.relationships: List[Tuple[int, int]] = []  # (parent_id, child_id)

    def add_member(
        self,
        member_id: int,
        name: str,
        generation_level: int,
        relationship: str,
        date_of_birth: Optional[date] = None,
        date_of_death: Optional[date] = None,
    ) -> None:
        """Add family member to tree"""

        self.members[member_id] = FamilyMemberNode(
            member_id=member_id,
            name=name,
            generation_level=generation_level,
            relationship=relationship,
            date_of_birth=date_of_birth,
            date_of_death=date_of_death,
            is_alive=date_of_death is None,
        )

    def add_relationship(self, parent_id: int, child_id: int) -> None:
        """Add parent-child relationship"""
        self.relationships.append((parent_id, child_id))

    def get_tree_visualization(self) -> Dict:
        """
        Generate tree visualization data.

        Returns:
            Dictionary with nodes and edges for visualization
        """

        nodes = []
        for member_id, member in self.members.items():
            nodes.append({
                "id": str(member_id),
                "label": member.name,
                "title": f"{member.relationship}, Gen {member.generation_level}",
                "generation": member.generation_level,
                "born": member.date_of_birth.isoformat() if member.date_of_birth else None,
                "died": member.date_of_death.isoformat() if member.date_of_death else None,
                "alive": member.is_alive,
            })

        edges = []
        for parent_id, child_id in self.relationships:
            edges.append({
                "from": str(parent_id),
                "to": str(child_id),
                "arrows": "to",
                "label": "parent-child",
            })

        return {
            "visualization_type": "family_tree",
            "nodes": nodes,
            "edges": edges,
            "total_members": len(self.members),
            "generations": self._get_generation_count(),
        }

    def get_descendants(self, ancestor_id: int) -> List[Dict]:
        """Get all descendants of a family member"""

        descendants = []
        self._traverse_descendants(ancestor_id, descendants)

        return sorted(descendants, key=lambda x: x["generation_level"])

    def get_ancestors(self, descendant_id: int) -> List[Dict]:
        """Get all ancestors of a family member"""

        ancestors = []
        self._traverse_ancestors(descendant_id, ancestors)

        return sorted(ancestors, key=lambda x: x["generation_level"])

    def get_siblings(self, member_id: int) -> List[Dict]:
        """Get siblings of a family member"""

        # Find parent relationships
        parents = []
        for parent_id, child_id in self.relationships:
            if child_id == member_id:
                parents.append(parent_id)

        # Find other children of same parents
        siblings = []
        for parent_id in parents:
            for p_id, child_id in self.relationships:
                if p_id == parent_id and child_id != member_id:
                    if child_id in self.members:
                        siblings.append({
                            "member_id": child_id,
                            "name": self.members[child_id].name,
                            "generation_level": self.members[child_id].generation_level,
                        })

        return siblings

    def calculate_gst_generation_levels(self) -> Dict[int, int]:
        """
        Calculate GST generation levels for all members.

        Generation levels for GST:
        - 0 = Transferor (primary person)
        - 1 = Direct descendants (children)
        - 2 = Grandchildren
        - 3+ = More distant

        Returns:
            Dictionary mapping member_id to GST generation level
        """

        gst_levels = {}

        # Assign based on relationship chain
        for member_id, member in self.members.items():
            gst_levels[member_id] = member.generation_level

        return gst_levels

    def identify_skip_persons(self, transferor_id: int) -> List[int]:
        """
        Identify skip persons for GST tax purposes.

        Skip persons are more than one generation below transferor.

        Args:
            transferor_id: ID of person making transfer

        Returns:
            List of skip person IDs
        """

        if transferor_id not in self.members:
            return []

        transferor_gen = self.members[transferor_id].generation_level
        descendants = self.get_descendants(transferor_id)

        skip_persons = [
            d["member_id"] for d in descendants
            if d["generation_level"] > transferor_gen + 1
        ]

        return skip_persons

    def create_inheritance_tree(self) -> Dict:
        """
        Create inheritance/distribution tree showing asset flow.

        Returns:
            Tree showing how assets pass to beneficiaries
        """

        # Build inheritance structure
        inheritance_structure = {}

        for member_id, member in self.members.items():
            # Find who this person inherits from
            inherits_from = []
            for parent_id, child_id in self.relationships:
                if child_id == member_id:
                    if parent_id in self.members:
                        inherits_from.append(self.members[parent_id].name)

            inheritance_structure[member.name] = {
                "inherits_from": inherits_from,
                "generation": member.generation_level,
                "assets_value": member.assets_to_inherit,
            }

        return {
            "inheritance_structure": inheritance_structure,
            "total_beneficiaries": len(self.members),
        }

    def get_family_statistics(self) -> Dict:
        """Get statistics about the family"""

        living_members = sum(1 for m in self.members.values() if m.is_alive)
        deceased_members = len(self.members) - living_members
        generations = self._get_generation_count()

        avg_assets = (
            sum(m.assets_to_inherit for m in self.members.values()) / len(self.members)
            if self.members else 0
        )

        return {
            "total_members": len(self.members),
            "living_members": living_members,
            "deceased_members": deceased_members,
            "generations_represented": generations,
            "average_assets_per_member": avg_assets,
            "total_assets": sum(m.assets_to_inherit for m in self.members.values()),
        }

    def export_gedcom(self) -> str:
        """
        Export family tree in GEDCOM format (genealogy standard).

        Returns:
            GEDCOM formatted string
        """

        gedcom = "0 HEAD\n"
        gedcom += "1 CHAR UTF-8\n"
        gedcom += "1 DATE " + date.today().isoformat() + "\n"

        # Add individuals
        for member_id, member in self.members.items():
            gedcom += f"0 @I{member_id}@ INDI\n"
            gedcom += f"1 NAME {member.name}\n"

            if member.date_of_birth:
                gedcom += f"1 BIRT\n2 DATE {member.date_of_birth.isoformat()}\n"

            if member.date_of_death:
                gedcom += f"1 DEAT\n2 DATE {member.date_of_death.isoformat()}\n"

        # Add family relationships
        for parent_id, child_id in self.relationships:
            gedcom += f"0 @F{parent_id}_{child_id}@ FAM\n"
            gedcom += f"1 HUSB @I{parent_id}@\n"
            gedcom += f"1 CHIL @I{child_id}@\n"

        gedcom += "0 TRLR\n"
        return gedcom

    def find_common_ancestor(self, member1_id: int, member2_id: int) -> Optional[Dict]:
        """Find the most recent common ancestor between two family members"""

        ancestors1 = self.get_ancestors(member1_id)
        ancestors2 = self.get_ancestors(member2_id)

        # Find common ancestors
        ancestor_ids_1 = set(a["member_id"] for a in ancestors1)
        ancestor_ids_2 = set(a["member_id"] for a in ancestors2)
        common_ids = ancestor_ids_1 & ancestor_ids_2

        if not common_ids:
            return None

        # Return the most recent (lowest generation)
        common_ancestors = [a for a in ancestors1 if a["member_id"] in common_ids]
        common_ancestors.sort(key=lambda x: x["generation_level"])

        return common_ancestors[0] if common_ancestors else None

    def calculate_inheritance_distribution(
        self,
        decedent_id: int,
        total_estate_value: float,
    ) -> Dict:
        """
        Calculate how estate would be distributed per family member.

        Args:
            decedent_id: ID of person whose estate is being distributed
            total_estate_value: Total estate value

        Returns:
            Distribution calculations for each beneficiary
        """

        descendants = self.get_descendants(decedent_id)

        if not descendants:
            return {"error": "No descendants found"}

        # Simple per-stirpes distribution (each line of descent gets equal share)
        distributions = {}

        for descendant in descendants:
            # Simplified calculation - could be more complex
            share = total_estate_value / len(descendants)

            distributions[descendant["member_id"]] = {
                "name": self.members[descendant["member_id"]].name,
                "relationship": self.members[descendant["member_id"]].relationship,
                "generation": descendant["generation_level"],
                "inheritance_share": share,
                "share_percentage": (share / total_estate_value * 100) if total_estate_value > 0 else 0,
            }

        return {
            "decedent": self.members[decedent_id].name if decedent_id in self.members else "Unknown",
            "total_estate": total_estate_value,
            "distribution_method": "per_stirpes",
            "beneficiary_distributions": distributions,
            "distribution_summary": self._summarize_distribution(distributions),
        }

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _traverse_descendants(self, ancestor_id: int, result: List[Dict]) -> None:
        """Recursively traverse descendants"""

        for parent_id, child_id in self.relationships:
            if parent_id == ancestor_id and child_id in self.members:
                member = self.members[child_id]
                result.append({
                    "member_id": child_id,
                    "name": member.name,
                    "generation_level": member.generation_level,
                    "relationship": member.relationship,
                })
                self._traverse_descendants(child_id, result)

    def _traverse_ancestors(self, descendant_id: int, result: List[Dict]) -> None:
        """Recursively traverse ancestors"""

        for parent_id, child_id in self.relationships:
            if child_id == descendant_id and parent_id in self.members:
                member = self.members[parent_id]
                result.append({
                    "member_id": parent_id,
                    "name": member.name,
                    "generation_level": member.generation_level,
                    "relationship": member.relationship,
                })
                self._traverse_ancestors(parent_id, result)

    def _get_generation_count(self) -> int:
        """Get number of generations in tree"""
        if not self.members:
            return 0
        return max(m.generation_level for m in self.members.values())

    @staticmethod
    def _summarize_distribution(distributions: Dict) -> Dict:
        """Summarize distribution across groups"""

        total_distributed = sum(
            d["inheritance_share"] for d in distributions.values()
        )

        return {
            "total_beneficiaries": len(distributions),
            "total_distributed": total_distributed,
            "average_per_beneficiary": (
                total_distributed / len(distributions) if distributions else 0
            ),
        }
