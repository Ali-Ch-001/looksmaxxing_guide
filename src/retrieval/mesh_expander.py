"""Dynamic MeSH (Medical Subject Headings) Query Expansion.

Autonomously maps colloquial aesthetic terms and active compounds to official
National Library of Medicine (NLM) controlled vocabulary descriptors
when search queries yield low citation density.
"""

from typing import List, Dict, Tuple, Set
import re

# Controlled vocabulary mappings to NLM MeSH Descriptors
MESH_DESCRIPTOR_MAP: Dict[str, str] = {
    # Trichology / Hair Loss
    "hair loss": '("Alopecia"[Mesh] OR "Hypotrichosis"[Mesh])',
    "hair thinning": '("Alopecia"[Mesh])',
    "balding": '("Alopecia, Androgenetic"[Mesh])',
    "androgenetic alopecia": '("Alopecia, Androgenetic"[Mesh])',
    "minoxidil": '("Minoxidil"[Mesh])',
    "oral minoxidil": '("Minoxidil"[Mesh] AND "Administration, Oral"[Mesh])',
    "topical minoxidil": '("Minoxidil"[Mesh] AND "Administration, Topical"[Mesh])',
    "finasteride": '("Finasteride"[Mesh] OR "5-alpha Reductase Inhibitors"[Mesh])',
    "dutasteride": '("Dutasteride"[Mesh] OR "5-alpha Reductase Inhibitors"[Mesh])',

    # Dermatology & Skincare
    "acne": '("Acne Vulgaris"[Mesh])',
    "pimples": '("Acne Vulgaris"[Mesh])',
    "tretinoin": '("Tretinoin"[Mesh] OR "Retinoids"[Mesh])',
    "retinoid": '("Retinoids"[Mesh])',
    "retin a": '("Tretinoin"[Mesh])',
    "adapalene": '("Adapalene"[Mesh] OR "Retinoids"[Mesh])',
    "differin": '("Adapalene"[Mesh])',
    "photoaging": '("Skin Aging"[Mesh] OR "Rejuvenation"[Mesh])',
    "wrinkles": '("Skin Aging"[Mesh])',
    "sunscreen": '("Sunscreening Agents"[Mesh] OR "Radiation Protection"[Mesh])',
    "spf": '("Sunscreening Agents"[Mesh])',
    "glycolic acid": '("Glycolic Acid"[Mesh] OR "Chemexfoliation"[Mesh])',
    "salicylic acid": '("Salicylic Acid"[Mesh] OR "Keratolytic Agents"[Mesh])',
    "microneedling": '("Needles"[Mesh] AND "Collagen"[Mesh])',
    "derma roller": '("Collagen"[Mesh] AND "Transdermal Administration"[Mesh])',

    # Orthodontics & Craniofacial
    "mewing": '("Tongue"[Mesh] AND ("Dental Occlusion"[Mesh] OR "Orthodontics"[Mesh]))',
    "tongue posture": '("Tongue"[Mesh] AND "Dental Occlusion"[Mesh])',
    "palate expansion": '("Palatal Expansion Technique"[Mesh])',
    "jawline": '("Mandible"[Mesh] OR "Dental Occlusion"[Mesh])',
    "malocclusion": '("Malocclusion"[Mesh])',
}


class MeSHQueryExpander:
    """Expands layperson and cosmetic queries with formal MeSH syntax."""

    @classmethod
    def expand(cls, raw_query: str) -> Tuple[str, List[str]]:
        lowered = raw_query.lower().strip()
        matched_mesh_terms: List[str] = []
        matched_mesh_clauses: List[str] = []

        # Find longest matching descriptors first
        for key in sorted(MESH_DESCRIPTOR_MAP.keys(), key=lambda k: len(k), reverse=True):
            if key in lowered:
                matched_mesh_terms.append(key)
                matched_mesh_clauses.append(MESH_DESCRIPTOR_MAP[key])
                # Remove matched phrase to prevent redundant sub-matches
                lowered = lowered.replace(key, " ")

        if not matched_mesh_clauses:
            return raw_query, []

        mesh_clause = " OR ".join(matched_mesh_clauses)
        expanded_query = f"({raw_query}) OR ({mesh_clause})"
        return expanded_query, matched_mesh_terms
