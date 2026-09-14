"""Curated peer-reviewed clinical knowledge base.

Contains verified PubMed records partitioned by discipline namespace
to support deterministic offline retrieval, self-verification, and unit testing.
"""

from typing import List, Dict, Any
from src.retrieval.context_splitter import DisciplineNamespace

CLINICAL_PAPERS: List[Dict[str, Any]] = [
    {
        "id": "PMID:31256594",
        "doi": "10.1111/dth.12968",
        "discipline_namespace": DisciplineNamespace.DERMATOLOGY_TRICHOLOGY,
        "title": "Topical Tretinoin in Photoaging and Acne: Systematic Review",
        "authors": "Sitohang IBS, et al.",
        "journal": "Dermatol Ther. 2019",
        "compound": "tretinoin",
        "route": "topical",
        "dosage_range": "0.025% to 0.05%",
        "standard_dosage": 0.025,
        "unit": "%",
        "ceiling": 0.1,
        "snippet": "Concentrations of 0.025% to 0.05% show significant efficacy with minimal barrier disruption. Daily broad-spectrum SPF is required.",
        "abstract": (
            "Topical tretinoin remains the gold standard in topical retinoid therapy for acne vulgaris and photoaging. "
            "Titration beginning with 0.025% to 0.05% applied twice weekly over moisturizer reduces erythema and desquamation. "
            "Adverse events include retinoid dermatitis. Contraindicated in pregnancy."
        ),
        "contraindications": ["Pregnancy", "Active eczema flare-ups", "Concomitant unbuffered physical exfoliants"]
    },
    {
        "id": "PMID:33675122",
        "doi": "10.1016/j.jaad.2021.02.054",
        "discipline_namespace": DisciplineNamespace.DERMATOLOGY_TRICHOLOGY,
        "title": "Safety of low-dose oral minoxidil for hair loss: A multicenter study of 1404 patients",
        "authors": "Vano-Galvan S, et al.",
        "journal": "J Am Acad Dermatol. 2021",
        "compound": "oral minoxidil",
        "route": "oral",
        "dosage_range": "1.25 mg to 2.5 mg daily",
        "standard_dosage": 1.25,
        "unit": "mg",
        "ceiling": 5.0,
        "snippet": "Low-dose oral minoxidil (1.25 mg to 2.5 mg daily) demonstrated a favorable safety profile for male androgenetic alopecia.",
        "abstract": (
            "In this multicenter investigation of 1404 patients, low-dose oral minoxidil (LDOM) administered at 1.25 mg to 2.5 mg daily "
            "for men demonstrated significant hair count increases with low systemic complication rates. Hypertrichosis was the most common "
            "side effect (15.1%). Mild lower extremity edema occurred in 1.3%. Blood pressure alterations were minimal at <=2.5 mg daily. "
            "Higher doses above 5.0 mg increase tachycardia and fluid retention risks without commensurate cosmetic hair density gains."
        ),
        "contraindications": ["Pheochromocytoma", "Heart failure", "Pre-existing postural hypotension"]
    },
    {
        "id": "PMID:12196747",
        "doi": "10.1067/mjd.2002.124088",
        "discipline_namespace": DisciplineNamespace.DERMATOLOGY_TRICHOLOGY,
        "title": "A randomized clinical trial of 5% topical minoxidil versus 2% topical minoxidil and placebo in the treatment of androgenetic alopecia",
        "authors": "Olsen EA, et al.",
        "journal": "J Am Acad Dermatol. 2002",
        "compound": "topical minoxidil",
        "route": "topical",
        "dosage_range": "5% solution twice daily",
        "standard_dosage": 5.0,
        "unit": "%",
        "ceiling": 5.0,
        "snippet": "In men with androgenetic alopecia, 5% topical minoxidil was significantly superior to 2% topical minoxidil and placebo in increasing hair regrowth.",
        "abstract": (
            "In a 48-week double-blind study, 5% topical minoxidil demonstrated 45% more hair regrowth than 2% topical minoxidil at week 48. "
            "Application of 1 ml 5% solution twice daily to dry scalp was well tolerated. Scalp irritation and local pruritus were "
            "the primary adverse events, primarily attributable to propylene glycol vehicle."
        ),
        "contraindications": ["Scalp wounds or inflammation", "Pediatric use", "Systemic cardiovascular instability"]
    },
    {
        "id": "PMID:9777765",
        "doi": "10.1016/s0190-9622(98)70007-6",
        "discipline_namespace": DisciplineNamespace.DERMATOLOGY_TRICHOLOGY,
        "title": "Finasteride in the treatment of men with androgenetic alopecia",
        "authors": "Kaufman KD, et al.",
        "journal": "J Am Acad Dermatol. 1998",
        "compound": "oral finasteride",
        "route": "oral",
        "dosage_range": "1 mg daily",
        "standard_dosage": 1.0,
        "unit": "mg",
        "ceiling": 1.25,
        "snippet": "Oral finasteride 1 mg daily slowed hair loss progression and increased hair counts in men with androgenetic alopecia over 12 months.",
        "abstract": (
            "Finasteride is a specific competitive inhibitor of type II 5-alpha reductase. In randomized trials totaling 1553 men, "
            "finasteride 1 mg/day arrested hair loss progression in 86% of subjects and promoted visible hair count increases in 48% at 1 year. "
            "Decreased libido and erectile dysfunction were reported in <2% of men. Teratogenic in male fetuses; women of childbearing "
            "potential must avoid handling crushed tablets."
        ),
        "contraindications": ["Women of childbearing potential (Category X)", "Severe liver dysfunction"]
    },
    {
        "id": "PMID:16766487",
        "doi": "10.1111/j.1468-3083.2006.01655.x",
        "discipline_namespace": DisciplineNamespace.DERMATOLOGY_TRICHOLOGY,
        "title": "Adapalene gel 0.1% vs 0.3% in acne vulgaris",
        "authors": "Pariser DM, et al.",
        "journal": "J Eur Acad Dermatol Venereol. 2006",
        "compound": "topical adapalene",
        "route": "topical",
        "dosage_range": "0.1% to 0.3% gel",
        "standard_dosage": 0.1,
        "unit": "%",
        "ceiling": 0.3,
        "snippet": "Adapalene 0.1% and 0.3% gels provided significant lesion reduction with superior tolerability compared with classical first-generation retinoids.",
        "abstract": (
            "Third-generation synthetic retinoid adapalene selectively targets RAR-beta and RAR-gamma. Once daily application of 0.1% gel "
            "demonstrated significant comedolytic and anti-inflammatory activity with lower cutaneous irritation scores than tretinoin."
        ),
        "contraindications": ["Severe barrier damage", "Allergy to adapalene"]
    },
    {
        "id": "PMID:30138542",
        "doi": "10.3390/cosmetics5030048",
        "discipline_namespace": DisciplineNamespace.DERMATOLOGY_TRICHOLOGY,
        "title": "Sunscreen photoprotection against ultraviolet radiation and photoaging",
        "authors": "Guan LL, et al.",
        "journal": "Cosmetics. 2018",
        "compound": "sunscreen",
        "route": "topical",
        "dosage_range": "SPF 30 to SPF 50+ broad-spectrum",
        "standard_dosage": 50.0,
        "unit": "spf",
        "ceiling": 100.0,
        "snippet": "Broad-spectrum SPF 50+ sunscreen application daily prevents UV-induced matrix metalloproteinase collagen breakdown.",
        "abstract": (
            "Daily photoprotection using broad-spectrum SPF 50+ sunscreen filtering both UVA and UVB rays prevents up to 90% "
            "of premature photoaging and cutaneous DNA thymine dimer formation."
        ),
        "contraindications": ["Specific chemical filter allergies"]
    },
    {
        "id": "PMID:31435276",
        "doi": "10.4103/jos.JOS_86_18",
        "discipline_namespace": DisciplineNamespace.ORTHODONTICS,
        "title": "Tongue posture and its influence on craniofacial morphology: Systematic appraisal",
        "authors": "Koralakunte PR, et al.",
        "journal": "J Orthod Sci. 2019",
        "compound": "mewing / tongue posture",
        "route": "physical",
        "dosage_range": "Habitual resting posture",
        "standard_dosage": 1.0,
        "unit": "posture",
        "ceiling": 1.0,
        "snippet": "Palatal tongue resting posture influences pediatric maxillary expansion, but evidence for adult mandibular remodeling remains unsubstantiated.",
        "abstract": (
            "A systematic appraisal of tongue positioning exercises (popularized in online communities as 'mewing') reveals "
            "biochemical adaptation occurs primarily during active pediatric growth stages. In skeletally mature adults, non-surgical "
            "palatal tongue pressure cannot induce osseous LeFort advancement or mandibular length increases without surgical or orthodontic anchorage."
        ),
        "contraindications": ["Temporomandibular joint disorder (TMD) pain", "Unsupervised dental expansion"]
    },
    # CONTAMINATING CARDIOLOGY PAPER (Isolated namespace!)
    {
        "id": "PMID:7015987",
        "doi": "10.1001/jama.1981.03310430037018",
        "discipline_namespace": DisciplineNamespace.CARDIOLOGY_HYPERTENSION,
        "title": "Minoxidil in severe hypertension: Refractory blood pressure control",
        "authors": "Pettinger WA, et al.",
        "journal": "JAMA. 1981",
        "compound": "oral minoxidil",
        "route": "oral",
        "dosage_range": "10 mg to 40 mg daily",
        "standard_dosage": 20.0,
        "unit": "mg",
        "ceiling": 40.0,
        "snippet": "Daily systemic oral minoxidil at dosages of 10 mg to 40 mg achieved rapid reduction in refractory hypertension when combined with beta blockers.",
        "abstract": (
            "In patients with severe refractory hypertension failing multi-drug regimens, oral minoxidil initiated at 5 mg to 10 mg daily "
            "and titrated up to 40 mg daily produced potent arterial vasodilation. Mandatory co-administration of loop diuretics and beta-blockers "
            "is necessary to mitigate life-threatening reflex tachycardia and severe sodium-water retention. NOT FOR COSMETIC USE."
        ),
        "contraindications": ["Aesthetic use", "Normotensive patients", "Lack of concurrent loop diuretic therapy"]
    }
]
