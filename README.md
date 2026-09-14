# Evidence-Led SEO Content Engine & Clinical Harm-Reduction Pipeline

An automated, deterministic, citation-grounded content pipeline architected to generate patient-facing clinical guides for answer engines (Perplexity, SearchGPT, Google) while eliminating medical misinformation, dangerous community practices (e.g. bone-smashing, unmonitored finasteride mega-dosing), and context drift.

---

## Architecture Diagram

```
[ Ingest & User Intent ]
         │
         ▼
[ Layer 1: Safety & Topic Triage ] ──(Banned / Dysmorphia)──► [ Route to Harm-Reduction / Crisis Notice ]
         │ (Safe Clinical Subject)
         ▼
[ Context-Split PubMed Retrieval ] ──(Namespace Isolation: Dermatology/Trichology vs Cardiology)
         │
         ▼
[ Structured Extraction Agent ] ────► [ Machine-Readable Evidence Matrix ]
         │
         ▼
[ Dual-Constraint Drafting Agent ]
  ├─ Target 1: Algorithmic Clarity (Schema.org, Perplexity citation density)
  └─ Target 2: Objective Demystification (Zero incel jargon, no toxic framing)
         │
         ▼
[ Layer 2: Deterministic Verification Gate ]
  ├─ 1. Regex AST Unit & Dosage Range Engine (Hard clinical bounds <= lookup ceiling)
  ├─ 2. 1:1 Citation Grounding Verifier (Exact substring & PMID cross-reference)
  ├─ 3. Post-Draft Toxic Slang & Dysmorphia Scan
  └─ 4. Schema.org JSON-LD Validator (MedicalWebPage + FAQPage)
         │
         ├──(Validation Fails: Hard Bound Exceeded)──► [ Immediate Unrecoverable Halt ]
         ├──(Validation Fails: Minor Defect)─────────► [ Max 2 Critique/Repair Loops ] ──► (Fail: Human Review Queue)
         │
         ▼ (Validation Passes)
[ Immutable State Persistence ] ───────────────────────► [ Append-Only SQLite Audit Ledger ]
         │
         ▼
[ Headless CMS / Static Site Generator Deployment ] ───► [ Markdown + Embedded Schema.org JSON-LD ]
```

---

## Failure Autopsy & Remediations Implemented

| Vulnerability from Failure Autopsy | Root Cause Identified | Engineering Remediation in this Pipeline |
| :--- | :--- | :--- |
| **Oral minoxidil 10 mg/day recommended for hair loss** (hypertensive dose leak) | Vector Search Context Contamination from general pharmacology index where cardiology chunks matched "minoxidil clinical efficacy". | **Discipline Context Splitting** (`src/retrieval/context_splitter.py`): Dermatology/Trichology indexes are strictly isolated from Cardiology. Hypertensive search results are purged before extraction. |
| **Article passed LLM-as-a-judge critique** | Weak LLM Critic (Self-Correction Fallacy): The LLM critic verified 10mg because the source chunk legitimately discussed 10mg for hypertension. | **Deterministic AST Range Engine** (`src/safety/dosage_checker.py`): Decoupled numerical verification from LLMs. Regex AST checks extract numeric values and compare them against hard clinical lookup ceilings (`CLINICAL_DICTIONARY`). |
| **Lack of boundary assertions** | No deterministic verification for units or route mismatches. | **Hard-Coded Posological Bounds**: Oral minoxidil max = 5.0 mg; topical minoxidil max = 5.0%; oral finasteride max = 1.25 mg; tretinoin max = 0.1%. Values exceeding this trigger immediate halts. |
| **Deployment without regression safety** | Lack of negative assertion testing. | **50 Automated Adversarial Test Cases** (`tests/test_negative_evals_50.py`): 100% rejection rate enforced by continuous testing. |

---

## Core Components & File Structure

```
looksmaxxing_guide/
├── README.md
├── pyproject.toml
├── src/
│   ├── schemas/
│   │   ├── pipeline_state.py      # PipelineState, ArticleDraft, EvidenceMatrix, AuditGateResult
│   │   └── schema_org.py          # Schema.org MedicalWebPage and FAQPage models
│   ├── safety/
│   │   ├── clinical_dictionary.py  # Hard clinical dosage boundaries & ceilings
│   │   ├── triage.py              # Layer 1 fuzzy matching, banned practices & crisis routing
│   │   └── dosage_checker.py      # Regex AST unit & posological range engine
│   ├── retrieval/
│   │   ├── context_splitter.py    # Namespace isolation & exclusionary boolean query filters
│   │   ├── knowledge_base.py      # Curated peer-reviewed clinical abstracts
│   │   └── pubmed_client.py       # PubMed search client with discipline filtering
│   ├── extraction/
│   │   └── evidence_matrix.py     # Structured extraction of mechanisms, dosages, and PMIDs
│   ├── drafting/
│   │   ├── prompt_templates.py    # Dual-constraint system prompts
│   │   └── dual_constraint_agent.py # High citation density + zero toxic framing
│   ├── verification/
│   │   ├── citation_verifier.py   # 1:1 PMID citation grounding verifier
│   │   ├── toxic_detector.py      # Post-drafting subculture slang & dysmorphia scanner
│   │   ├── schema_validator.py    # Schema.org JSON-LD validator
│   │   └── gate_engine.py         # Multi-check gate orchestrator with repair loops
│   ├── persistence/
│   │   ├── db.py                  # SQLite append-only audit trail
│   │   └── state_graph.py         # Checkpointing and idempotency key manager
│   ├── deployment/
│   │   └── cms_exporter.py        # Markdown + JSON-LD frontmatter exporter
│   └── pipeline/
│       └── orchestrator.py        # End-to-end evidence-led SEO engine
└── tests/
    ├── test_negative_evals_50.py   # 50 adversarial negative test cases (100% rejection rate)
    ├── test_triage_safety.py       # Layer 1 safety triage tests
    ├── test_dosage_bounds.py       # Deterministic dosage engine unit tests
    ├── test_citation_grounding.py  # 1:1 Citation grounding tests
    ├── test_schema_org.py          # Schema.org JSON-LD compliance tests
    ├── test_repair_loop.py         # Critique and repair loop tests
    ├── test_persistence.py         # SQLite audit snapshot and idempotency tests
    └── test_end_to_end_pipeline.py # End-to-end integration tests
```

---

## Running the Verification Suite

```bash
# Run all 73 tests (including the 50 negative evaluation test cases)
pytest -v
```
