"""Hard-coded clinical dosage boundaries and absolute safety ceilings.

Decoupled from LLM judgment to prevent context drift and silent assertion failures.
Derived from FDA indications, British Association of Dermatologists (BAD),
and American Academy of Dermatology (AAD) consensus guidelines.
"""

from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field
from src.safety.triage import _normalize_text, _compact_alphanumeric


class ClinicalDosageCeiling(BaseModel):
    canonical_name: str
    aliases: List[str]
    route: Literal["oral", "topical", "physical", "systemic"]
    unit: str
    absolute_ceiling: float
    standard_min: float
    standard_max: float
    clinical_discipline: str = "Dermatology/Trichology"
    indication: str
    absolute_contraindications: List[str] = Field(default_factory=list)
    failure_risk_tag: str
    warning_threshold: Optional[float] = None


# Clinical lookup table: Hard limits for aesthetic/dermatological use
CLINICAL_DICTIONARY: Dict[str, ClinicalDosageCeiling] = {
    "oral_minoxidil": ClinicalDosageCeiling(
        canonical_name="oral_minoxidil",
        aliases=["oral minoxidil", "systemic minoxidil", "loniten", "minoxidil tablet", "minoxidil pill", "oral minox"],
        route="oral",
        unit="mg",
        absolute_ceiling=5.0,  # Max off-label hair dose. 10mg+ is refractory hypertension dose.
        standard_min=0.625,
        standard_max=2.5,
        warning_threshold=2.5,
        clinical_discipline="Dermatology/Trichology",
        indication="Androgenetic Alopecia",
        absolute_contraindications=[
            "Pheochromocytoma",
            "Congestive heart failure",
            "Severe angina pectoris",
            "Pericardial effusion",
            "Normotensive individuals without cardiovascular baseline"
        ],
        failure_risk_tag="CARDIOVASCULAR_HYPERTENSIVE_OVERDOSE_DRIFT"
    ),
    "topical_minoxidil": ClinicalDosageCeiling(
        canonical_name="topical_minoxidil",
        aliases=["topical minoxidil", "rogaine", "regaine", "minoxidil solution", "minoxidil foam", "minoxidil 5%", "minoxidil 2%"],
        route="topical",
        unit="%",
        absolute_ceiling=5.0,  # 5% max standard OTC. 10%+ is unapproved compounding with systemic absorption risks.
        standard_min=2.0,
        standard_max=5.0,
        clinical_discipline="Dermatology/Trichology",
        indication="Androgenetic Alopecia",
        absolute_contraindications=[
            "Broken, irritated, or sunburned scalp",
            "Concurrent use of occlusive dressings without supervision",
            "Oral ingestion (extremely toxic)"
        ],
        failure_risk_tag="UNAPPROVED_TOPICAL_SUPERCONCENTRATION"
    ),
    "oral_finasteride": ClinicalDosageCeiling(
        canonical_name="oral_finasteride",
        aliases=["oral finasteride", "finasteride", "propecia", "proscar", "finasteride tablet"],
        route="oral",
        unit="mg",
        absolute_ceiling=1.25,  # 1mg daily is standard hair dose. 5mg is BPH (prostate) dose.
        standard_min=0.5,
        standard_max=1.0,
        warning_threshold=1.0,
        clinical_discipline="Dermatology/Trichology",
        indication="Male Androgenetic Alopecia",
        absolute_contraindications=[
            "Women of childbearing potential or pregnancy (teratogenic Category X)",
            "Severe hepatic insufficiency",
            "Pediatric patients under 18"
        ],
        failure_risk_tag="BPH_PROSTATE_DOSE_CONTAMINATION"
    ),
    "topical_finasteride": ClinicalDosageCeiling(
        canonical_name="topical_finasteride",
        aliases=["topical finasteride", "finasteride gel", "finasteride solution"],
        route="topical",
        unit="%",
        absolute_ceiling=0.25,
        standard_min=0.005,
        standard_max=0.25,
        clinical_discipline="Dermatology/Trichology",
        indication="Male Androgenetic Alopecia",
        absolute_contraindications=[
            "Pregnancy contact hazard (transdermal absorption)",
            "Active scalp dermatitis"
        ],
        failure_risk_tag="EXCESSIVE_TOPICAL_5AR_INHIBITION"
    ),
    "oral_dutasteride": ClinicalDosageCeiling(
        canonical_name="oral_dutasteride",
        aliases=["oral dutasteride", "dutasteride", "avodart"],
        route="oral",
        unit="mg",
        absolute_ceiling=0.5,
        standard_min=0.5,
        standard_max=0.5,
        clinical_discipline="Dermatology/Trichology",
        indication="Refractory Androgenetic Alopecia",
        absolute_contraindications=[
            "Women of childbearing potential or pregnancy",
            "Blood donation within 6 months of discontinuation",
            "Severe hepatic impairment"
        ],
        failure_risk_tag="EXCESSIVE_DUAL_5AR_INHIBITION"
    ),
    "topical_tretinoin": ClinicalDosageCeiling(
        canonical_name="topical_tretinoin",
        aliases=["topical tretinoin", "tretinoin", "retin-a", "all-trans retinoic acid", "tretinoin cream", "tretinoin gel"],
        route="topical",
        unit="%",
        absolute_ceiling=0.1,  # 0.1% is max prescription strength. Anything higher is chemical burn hazard.
        standard_min=0.025,
        standard_max=0.05,
        warning_threshold=0.05,
        clinical_discipline="Dermatology",
        indication="Acne Vulgaris & Photoaging",
        absolute_contraindications=[
            "Pregnancy and lactation",
            "Active eczema or cutaneous barrier impairment",
            "Concurrent use of harsh physical scrubs or unstabilized high-percentage acids"
        ],
        failure_risk_tag="CHEMICAL_BARRIER_STRIPPING_RISK"
    ),
    "topical_adapalene": ClinicalDosageCeiling(
        canonical_name="topical_adapalene",
        aliases=["topical adapalene", "adapalene", "differin"],
        route="topical",
        unit="%",
        absolute_ceiling=0.3,
        standard_min=0.1,
        standard_max=0.3,
        clinical_discipline="Dermatology",
        indication="Acne Vulgaris",
        absolute_contraindications=[
            "Severe compromised skin barrier",
            "Hypersensitivity to adapalene"
        ],
        failure_risk_tag="RETINOID_TOXICITY"
    ),
    "at_home_glycolic_acid": ClinicalDosageCeiling(
        canonical_name="at_home_glycolic_acid",
        aliases=["glycolic acid", "aha chemical peel", "glycolic peel", "at home peel"],
        route="topical",
        unit="%",
        absolute_ceiling=15.0,  # >15% is medical clinic only (30-70%), causes full-thickness chemical burns at home
        standard_min=5.0,
        standard_max=10.0,
        clinical_discipline="Dermatology",
        indication="Exfoliation & Keratinocyte Renewal",
        absolute_contraindications=[
            "Open wounds or active herpes simplex outbreaks",
            "Darker Fitzpatrick skin types without pre-treatment buffering (post-inflammatory hyperpigmentation risk)"
        ],
        failure_risk_tag="AT_HOME_CHEMICAL_BURN_RISK"
    ),
    "at_home_salicylic_acid": ClinicalDosageCeiling(
        canonical_name="at_home_salicylic_acid",
        aliases=["salicylic acid", "bha", "salicylic wash", "salicylic serum"],
        route="topical",
        unit="%",
        absolute_ceiling=2.0,  # 2% max OTC leave-on
        standard_min=0.5,
        standard_max=2.0,
        clinical_discipline="Dermatology",
        indication="Comedonal Acne & Sebum Regulation",
        absolute_contraindications=[
            "Aspirin (salicylate) hypersensitivity",
            "Application over widespread denuded areas (salicylism risk)"
        ],
        failure_risk_tag="SALICYLATE_TOXICITY_RISK"
    ),
    "at_home_microneedling": ClinicalDosageCeiling(
        canonical_name="at_home_microneedling",
        aliases=["microneedling", "derma roller", "derma stamp", "dermaroller", "needle length"],
        route="physical",
        unit="mm",
        absolute_ceiling=0.5,  # >0.5mm requires clinical asepsis, risk of granuloma and systemic infection
        standard_min=0.25,
        standard_max=0.5,
        clinical_discipline="Dermatology",
        indication="Transdermal Absorption & Collagen Induction",
        absolute_contraindications=[
            "Active cystic acne or bacterial infection",
            "Keloid scarring tendency",
            "Unsanitized reuse of needles"
        ],
        failure_risk_tag="DEEP_DERMAL_INFECTION_AND_FIBROSIS"
    ),
}


def find_clinical_bound(text: str, route_hint: Optional[str] = None) -> Optional[ClinicalDosageCeiling]:
    """Resolves a compound mentioned in text to its clinical dosage boundary contract."""
    lowered = _normalize_text(text)
    compact = _compact_alphanumeric(text)
    
    # Check oral vs topical minoxidil explicitly
    if any(k in lowered or k in compact for k in ["minoxidil", "minox", "loniten", "rogaine"]):
        is_oral = route_hint == "oral" or any(w in lowered or w in compact for w in ["oral", "pill", "tablet", "capsule", "systemic", "swallow", "ingest", "drink", "loniten"])
        is_topical = route_hint == "topical" or any(w in lowered or w in compact for w in ["topical", "foam", "scalp", "apply", "rogaine"])
        if is_oral:
            return CLINICAL_DICTIONARY["oral_minoxidil"]
        if is_topical:
            return CLINICAL_DICTIONARY["topical_minoxidil"]
        # Default to oral if dosage unit is mg, topical if %
        return CLINICAL_DICTIONARY["oral_minoxidil"] if "mg" in lowered else CLINICAL_DICTIONARY["topical_minoxidil"]

    # Check finasteride
    if any(k in lowered or k in compact for k in ["finasteride", "propecia", "proscar"]):
        if "topical" in lowered or "topical" in compact or route_hint == "topical":
            return CLINICAL_DICTIONARY["topical_finasteride"]
        return CLINICAL_DICTIONARY["oral_finasteride"]

    # Check dutasteride
    if any(k in lowered or k in compact for k in ["dutasteride", "avodart"]):
        return CLINICAL_DICTIONARY["oral_dutasteride"]

    # Check tretinoin
    if any(k in lowered or k in compact for k in ["tretinoin", "retina", "retinoicacid"]):
        return CLINICAL_DICTIONARY["topical_tretinoin"]

    # Check adapalene
    if any(k in lowered or k in compact for k in ["adapalene", "differin"]):
        return CLINICAL_DICTIONARY["topical_adapalene"]

    # Check glycolic
    if "glycolic" in lowered or "glycolic" in compact:
        return CLINICAL_DICTIONARY["at_home_glycolic_acid"]

    # Check salicylic
    if "salicylic" in lowered or "salicylic" in compact or "bha" in lowered:
        return CLINICAL_DICTIONARY["at_home_salicylic_acid"]

    # Check microneedling / derma roller
    if any(k in lowered or k in compact for k in ["microneedl", "dermaroll", "dermastamp"]):
        return CLINICAL_DICTIONARY["at_home_microneedling"]

    return None
