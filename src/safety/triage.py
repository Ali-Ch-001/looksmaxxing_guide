"""Layer 1: Pre-Execution Safety & Topic Triage Gate.

Fuzzy string-distance matching and token analysis against toxic subculture tropes,
self-harm practices, and body dysmorphia forum memes. Routes banned topics
immediately to crisis/harm-reduction resources before any LLM execution occurs.
"""

from __future__ import annotations
import re
import unicodedata
from typing import Dict, Any, List, Optional, Tuple
from src.schemas.pipeline_state import PipelineState, RiskCategory


# Prohibited physical trauma and dangerous grey-market practices
PROHIBITED_PATTERNS: List[Dict[str, Any]] = [
    {
        "id": "BONE_SMASHING",
        "keywords": [
            "bone smashing", "bone-smashing", "bone breaker", "bonesmashing",
            "hammering jaw", "hammering face", "face smashing", "chin hitting",
            "jaw hammering", "cheekbone hammering", "chin smashing", "hammering cheekbones"
        ],
        "harm_reduction_notice": (
            "Bone smashing (intentional blunt-force trauma to facial bones) does NOT cause controlled osteogenesis "
            "via Wolff's law. Instead, it produces comminuted micro-fractures, asymmetric fibrous malunion, "
            "chronic soft-tissue scarring, and irreversible trigeminal/mental nerve damage resulting in permanent numbness."
        ),
        "crisis_category": "self_harm_physical_trauma"
    },
    {
        "id": "DIY_SURGERY",
        "keywords": [
            "diy lefort", "lefort at home", "diy osteotomy", "self osteotomy",
            "diy orthognathic", "diy surgery", "diy canthoplasty", "diy rhinoplasty",
            "orbital decompression at home", "eyeball protrusion diy"
        ],
        "harm_reduction_notice": (
            "Attempting surgical osteotomies or soft-tissue modifications outside a sterile operating theatre "
            "carries an immediate risk of fatal arterial hemorrhage (maxillary artery laceration), catastrophic intracranial infection, "
            "permanent airway compromise, and irreversible facial deformity."
        ),
        "crisis_category": "self_harm_surgical"
    },
    {
        "id": "GREY_MARKET_HORMONES",
        "keywords": [
            "underground hgh", "black market hgh", "grey market peptide", "underground steroid",
            "unmonitored trt", "diy trt", "black market tren", "unregulated igf-1",
            "black market finasteride", "unmonitored mega dose"
        ],
        "harm_reduction_notice": (
            "Unregulated hormone products from subterranean suppliers frequently contain microbial endotoxins, "
            "incorrect active concentrations, heavy metals, or completely substituted compounds. Unmonitored administration "
            "induces secondary hypogonadism, left ventricular hypertrophy, polycythemia, and endocrine failure."
        ),
        "crisis_category": "substance_harm"
    },
    {
        "id": "CAUSTIC_CHEMICALS",
        "keywords": [
            "chlorine wash", "bleach wash", "caustic eye", "iris lightening drops",
            "chlorine skin bleaching", "phenol at home", "industrial acid peel"
        ],
        "harm_reduction_notice": (
            "Caustic agents such as chlorine or industrial-strength phenols applied to skin or eyes result in "
            "third-degree chemical liquefactive necrosis, permanent corneal blindness, and systemic cardiac toxicity."
        ),
        "crisis_category": "chemical_trauma"
    },
    {
        "id": "EXTREME_FASTING",
        "keywords": [
            "dry fasting 7 days", "severe dry fasting", "72 hour dry fast",
            "dry fasting for jawline", "extreme starvation diet", "eating disorder purge"
        ],
        "harm_reduction_notice": (
            "Severe prolonged dry fasting causes acute kidney injury, hypovolemic shock, lethal electrolyte dysregulation "
            "(hypokalemic cardiac arrhythmia), and irreversible renal tubular necrosis."
        ),
        "crisis_category": "eating_disorder"
    }
]

# Toxic incel slang and dysmorphia despair tropes
TOXIC_SUBCLUTURE_TROPES: List[str] = [
    "hunter eyes or rope",
    "it's over for",
    "subhuman skull",
    "chad or death",
    "subhuman chin",
    "currycel",
    "ricecel",
    "looksminning",
    "rope or cope",
    "subhuman tier",
    "subhuman jaw",
    "wrist size over"
]

CRISIS_RESOURCES = {
    "emergency": "If you are in immediate crisis or considering self-harm, call or text 988 (USA & Canada) or 111 (UK).",
    "body_dysmorphia": {
        "organization": "Body Dysmorphic Disorder Foundation",
        "url": "https://bddfoundation.org",
        "description": "Resources, clinical help, and peer support for appearance-related anxiety and obsessive body evaluation."
    },
    "eating_disorders": {
        "organization": "National Eating Disorders Association (NEDA)",
        "url": "https://www.nationaleatingdisorders.org",
        "contact": "Call/text 1-800-931-2237"
    }
}


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Computes Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


UNICODE_HOMOGLYPH_MAP = {
    # Cyrillic lookalikes
    'а': 'a', 'с': 'c', 'е': 'e', 'о': 'o', 'р': 'p', 'х': 'x',
    'у': 'y', 'і': 'i', 'ј': 'j', 'ѕ': 's', 'в': 'b', 'к': 'k',
    'м': 'm', 'н': 'h', 'т': 't', 'д': 'd', 'г': 'g', 'л': 'l',
    # Greek lookalikes
    'α': 'a', 'β': 'b', 'ε': 'e', 'η': 'n', 'ι': 'i', 'κ': 'k',
    'ν': 'v', 'ο': 'o', 'ρ': 'p', 'τ': 't', 'υ': 'u', 'χ': 'x', 'ω': 'w',
    # Common leetspeak substitutions
    '@': 'a', '4': 'a', '$': 's', '5': 's', '0': 'o', '1': 'i', '!': 'i',
    '3': 'e', '7': 't', '+': 't', '8': 'b', '_': ' ', '-': ' ', '/': ' '
}

ZERO_WIDTH_CHARS = {
    '\u200b', '\u200c', '\u200d', '\ufeff', '\u00ad', '\u2060',
    '\u2000', '\u2001', '\u2002', '\u2003', '\u2004', '\u2005',
    '\u2006', '\u2007', '\u2008', '\u2009', '\u200a', '\u2028', '\u2029'
}


def _normalize_text(text: str) -> str:
    """Multi-pass Unicode NFKD, zero-width stripping, and homoglyph de-obfuscation."""
    # 1. Unicode decomposition (NFKD) handles fullwidth characters and combined accents
    decomposed = unicodedata.normalize('NFKD', text)

    # 2. Strip zero-width and invisible characters
    cleaned_chars = [c for c in decomposed if c not in ZERO_WIDTH_CHARS]
    cleaned = "".join(cleaned_chars).lower()

    # 3. Apply homoglyph and leetspeak substitution map
    mapped_chars = [UNICODE_HOMOGLYPH_MAP.get(c, c) for c in cleaned]
    mapped_text = "".join(mapped_chars)

    # 4. Collapse punctuation and whitespaces
    mapped_text = re.sub(r'[^\w\s]', ' ', mapped_text)
    normalized = re.sub(r'\s+', ' ', mapped_text).strip()
    return normalized


def _compact_alphanumeric(text: str) -> str:
    """Returns contiguous lowercase alphanumeric characters for detecting space-injected evasions."""
    norm = _normalize_text(text)
    return re.sub(r'[^a-z0-9]', '', norm)


def check_banned_topic(raw_text: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Evaluates raw topic against prohibited patterns using exact, compact, and fuzzy matching.
    
    Returns: (is_banned, prohibited_pattern_dict, matched_phrase)
    """
    normalized = _normalize_text(raw_text)
    compact = _compact_alphanumeric(raw_text)

    # 1. Exact & substring check across prohibited patterns (normalized and compact)
    for pattern in PROHIBITED_PATTERNS:
        for kw in pattern["keywords"]:
            norm_kw = _normalize_text(kw)
            compact_kw = _compact_alphanumeric(kw)
            if norm_kw in normalized or compact_kw in compact:
                return True, pattern, kw

    # 2. Toxic incel despair tropes check
    for trope in TOXIC_SUBCLUTURE_TROPES:
        norm_trope = _normalize_text(trope)
        compact_trope = _compact_alphanumeric(trope)
        if norm_trope in normalized or compact_trope in compact:
            return True, {
                "id": "TOXIC_INSECURE_TROPE",
                "harm_reduction_notice": (
                    "Content containing fatalistic incel subculture tropes or dysmorphic despair language "
                    "is barred from automated generation to prevent reinforcing appearance-based psychological distress."
                ),
                "crisis_category": "body_dysmorphia"
            }, trope

    # 3. Fuzzy n-gram matching for obfuscated prohibited phrases & toxic tropes (e.g. 'b0ne smash1ng')
    words = normalized.split()
    for pattern in PROHIBITED_PATTERNS:
        for kw in pattern["keywords"]:
            kw_words = _normalize_text(kw).split()
            kw_len = len(kw_words)
            if len(words) >= kw_len:
                for i in range(len(words) - kw_len + 1):
                    window = " ".join(words[i:i + kw_len])
                    dist = _levenshtein_distance(window, " ".join(kw_words))
                    max_allowed = 1 if len(kw) < 12 else 2
                    if dist <= max_allowed:
                        return True, pattern, window

    for trope in TOXIC_SUBCLUTURE_TROPES:
        trope_words = _normalize_text(trope).split()
        t_len = len(trope_words)
        if len(words) >= t_len:
            for i in range(len(words) - t_len + 1):
                window = " ".join(words[i:i + t_len])
                dist = _levenshtein_distance(window, " ".join(trope_words))
                max_allowed = 1 if len(trope) < 12 else 2
                if dist <= max_allowed:
                    return True, {
                        "id": "TOXIC_INSECURE_TROPE",
                        "harm_reduction_notice": (
                            "Content containing fatalistic incel subculture tropes or dysmorphic despair language "
                            "is barred from automated generation to prevent reinforcing appearance-based psychological distress."
                        ),
                        "crisis_category": "body_dysmorphia"
                    }, window

    return False, None, None


class SafetyTriageAgent:
    """Pre-execution agent that enforces Layer 1 safety and topic classification."""

    @staticmethod
    def triage(state: PipelineState) -> PipelineState:
        state.normalized_topic = _normalize_text(state.raw_topic)
        state.step_history.append("step_1_classify_and_triage")

        # Check for banned self-harm or toxic tropes
        is_banned, matched_pattern, matched_phrase = check_banned_topic(state.raw_topic)
        if is_banned and matched_pattern:
            state.risk_category = "banned"
            state.audit_passed = False
            state.is_crisis_routed = True
            state.rejection_reason = (
                f"Prohibited practice or toxic subculture framing detected ('{matched_phrase}'). "
                f"Violation ID: {matched_pattern['id']}."
            )
            state.crisis_payload = {
                "violation_id": matched_pattern["id"],
                "trigger_phrase": matched_phrase,
                "harm_reduction_warning": matched_pattern["harm_reduction_notice"],
                "crisis_resources": CRISIS_RESOURCES
            }
            return state

        # Categorize legitimate clinical discipline
        lowered = state.normalized_topic
        if any(term in lowered for term in ["acne", "tretinoin", "retinoid", "skin", "minoxidil", "finasteride", "dutasteride", "hair", "scalp", "adapalene", "glycolic", "salicylic", "spf", "sunscreen", "microneedl"]):
            state.risk_category = "dermatology_trichology"
            state.discipline_namespace = "dermatology_trichology"
        elif any(term in lowered for term in ["jawline", "mewing", "palate", "teeth", "bite", "orthodontic", "malocclusion", "tongue posture"]):
            state.risk_category = "orthodontics"
            state.discipline_namespace = "orthodontics"
        elif any(term in lowered for term in ["posture", "body fat", "hypertrophy", "neck training", "exercise", "workout"]):
            state.risk_category = "fitness"
            state.discipline_namespace = "fitness"
        elif any(term in lowered for term in ["rhinoplasty", "blepharoplasty", "botox", "filler", "genioplasty", "surgical"]):
            state.risk_category = "surgical"
            state.discipline_namespace = "surgical"
        else:
            state.risk_category = "fitness"
            state.discipline_namespace = "general"

        state.audit_passed = True
        return state
