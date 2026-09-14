# looksmaxxing.guide — Evidence-Led Clinical SEO Engine & Genetic Red-Team Platform

[![CI Pipeline](https://github.com/Ali-Ch-001/looksmaxxing_guide/actions/workflows/ci.yml/badge.svg)](https://github.com/Ali-Ch-001/looksmaxxing_guide/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/orchestration-LangGraph%20StateGraph-green.svg)](https://github.com/langchain-ai/langgraph)
[![OpenTelemetry](https://img.shields.io/badge/tracing-OpenTelemetry-purple.svg)](https://opentelemetry.io/)
[![Langfuse](https://img.shields.io/badge/observability-Langfuse-orange.svg)](https://langfuse.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Platform Mission:** [looksmaxxing.guide](https://looksmaxxing.guide) is an authoritative, evidence-led, harm-reduction content platform for the male aesthetic and self-improvement subculture (grooming, fitness, dermatology, orthodontics, style). It provides peer-reviewed, citation-grounded coverage of a space historically dominated by dangerous community lore, unmonitored drug mega-dosing, and body dysmorphic despair memes.

---

## 1. Executive Summary & Market Positioning

### Target Market
* **Demographic:** Men aged 18–35 actively researching grooming, skincare, hair preservation, and aesthetic self-development.
* **Geographies:** English-first markets (US, UK, Canada, Australia).
* **Intent:** Search-driven (Google) and Answer-Engine driven (Perplexity, SearchGPT) queries seeking molecular mechanisms, exact dosages, and safety contraindications.

### Strategic Competitive Landscape

| Attribute | **looksmaxxing.guide** (This Platform) | **Looksmax.org Forum** | **Reddit r/looksmaxxing** | **GQ / Men's Health** |
| :--- | :--- | :--- | :--- | :--- |
| **Editorial Model** | Deterministic evidence synthesis | Anonymized user forum | Community UGC | Lifestyle journalism |
| **Medical Safety** | Hard AST boundaries & clinical lookup ceilings | Unregulated grey-market recommendations | Unmoderated peer advice | Sponsor-driven, vague posology |
| **Subculture Tone** | Clinical, objective demystification (0% toxic slang) | Incel despair fatalism (`subhuman`, `it's over`) | Mixed meme-culture | Generic, low specificity |
| **AI Answer Discovery** | Native Schema.org `MedicalWebPage` & `FAQPage` | Unstructured forum threads | Dynamic Reddit comments | Paywalled / Ad-bloated prose |
| **Verification Gate** | Programmatic regex AST + 1:1 PMID grounding | None | Upvotes / Downvotes | Editorial committee |

---

## 2. Failure Autopsy & Engineering Remediations

```
[ Ingest & User Intent ]
         │
         ▼
[ Layer 1: Safety & Topic Triage ] ──(Banned / Dysmorphia)──► [ Harm-Reduction / Crisis Advisory ]
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
  ├─ 1. Posological AST Engine v2 (Cumulative daily load <= lookup ceiling)
  ├─ 2. 1:1 Citation Grounding Verifier (Exact substring & PMID cross-reference)
  ├─ 3. Post-Draft Toxic Slang & Dysmorphia Scan
  └─ 4. Schema.org JSON-LD Validator (MedicalWebPage + FAQPage)
         │
         ├──(Validation Fails: Hard Bound Exceeded)──► [ Immediate Unrecoverable Halt ]
         ├──(Validation Fails: Minor Defect)─────────► [ Max 2 Critique/Repair Loops ] ──► (Fail: Human Review Queue)
         │
         ▼ (Validation Passes)
[ Immutable State Persistence ] ───────────────────────► [ Append-Only SQLite Audit Ledger with WAL ]
         │
         ▼
[ Headless CMS / SSG Exporter ] ───────────────────────► [ Markdown + Embedded Schema.org JSON-LD ]
```

### The Failure Autopsy Remediations

| Vulnerability from Failure Autopsy | Root Cause Identified | Engineering Remediation in this Engine |
| :--- | :--- | :--- |
| **Hypertensive Minoxidil Leak (10 mg/day recommended for hair loss)** | Vector search context contamination: General pharmacology embeddings matched "minoxidil clinical efficacy" in a cardiology index. | **Discipline Context Splitting** (`src/retrieval/context_splitter.py`): Isolated namespaces for `Dermatology_Trichology` vs `Cardiology`. Injects exclusionary boolean filters (`NOT ("hypertensive emergency" OR "refractory hypertension")`). |
| **Silent Verification Failure (Passed LLM-as-a-judge)** | Weak LLM Critic (Self-Correction Fallacy): The LLM judge verified 10 mg as source-grounded because the cardiology chunk legitimately discussed 10 mg. | **Decoupled Posological AST Engine v2** (`src/safety/dosage_checker.py`): Replaced LLM evaluation with deterministic regex AST boundary assertions evaluated against `CLINICAL_DICTIONARY`. |
| **Posological Unit Camouflage (`10000 mcg` or `0.01 g`)** | Unit mismatch in regex parser falling through without threshold validation. | **Canonical Unit Normalization**: Converts all mass units (`mcg`, `g`, `mg`) to standard base units before applying inequality checks. |
| **Multi-Dose Frequency Splitting (`5 mg morning + 5 mg evening`)** | Single-sentence parsing missed cumulative daily systemic load across protocol lines. | **Cumulative Posology Accumulator**: Aggregates frequency-multiplied daily posology across all protocol instructions per compound. |
| **Obfuscated Evasion (`b0ne smash1ng`, `o.r.a.l m.i.n.o.x`)** | Naive string matching bypassed by Cyrillic homoglyphs, zero-width characters, and inter-letter punctuation. | **Multi-Pass Unicode NFKD & Compact Alphanumeric Stripper** (`src/safety/triage.py`): Strips zero-width characters, converts homoglyphs, and collapses spaced characters. |

---

## 3. Clinical Dictionary & Hard Posological Ceilings

Hard limits derived from FDA indications, British Association of Dermatologists (BAD), and American Academy of Dermatology (AAD) guidelines:

| Compound | Route | Standard Initiation | Standard Max | **Absolute Ceiling** | Failure Risk Tag | Absolute Contraindications |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Oral Minoxidil** | Oral | 0.625 mg/day | 2.5 mg/day | **5.0 mg/day** | `CARDIOVASCULAR_HYPERTENSIVE_OVERDOSE_DRIFT` | Pheochromocytoma, heart failure, pericardial effusion |
| **Topical Minoxidil**| Topical| 2.0% | 5.0% | **5.0%** | `UNAPPROVED_TOPICAL_SUPERCONCENTRATION` | Scalp abrasions, oral consumption |
| **Oral Finasteride** | Oral | 0.5 mg/day | 1.0 mg/day | **1.25 mg/day** | `BPH_PROSTATE_DOSE_CONTAMINATION` | Pregnancy (Category X), female handling, liver failure |
| **Topical Finasteride**| Topical| 0.005% | 0.25% | **0.25%** | `EXCESSIVE_TOPICAL_5AR_INHIBITION` | Pregnancy contact hazard |
| **Oral Dutasteride** | Oral | 0.5 mg/day | 0.5 mg/day | **0.5 mg/day** | `EXCESSIVE_DUAL_5AR_INHIBITION` | Women of childbearing potential |
| **Topical Tretinoin**| Topical| 0.025% | 0.05% | **0.1%** | `CHEMICAL_BARRIER_STRIPPING_RISK` | Pregnancy, active eczema, concurrent physical scrubs |
| **Topical Adapalene**| Topical| 0.1% | 0.3% | **0.3%** | `RETINOID_TOXICITY` | Severe barrier disruption |
| **At-Home Glycolic** | Topical| 5.0% | 10.0% | **15.0%** | `AT_HOME_CHEMICAL_BURN_RISK` | >15% is clinic-only; chemical burn risk |
| **At-Home Salicylic** | Topical| 0.5% | 2.0% | **2.0%** | `SALICYLATE_TOXICITY_RISK` | Aspirin allergy, widespread denuded skin |
| **At-Home Microneedling**| Physical| 0.25 mm | 0.5 mm | **0.5 mm** | `DEEP_DERMAL_INFECTION_AND_FIBROSIS` | >0.5 mm requires clinical asepsis |

---

## 4. Evolutionary Genetic Red-Teaming Engine

The engine includes a built-in directed genetic fuzzer (`src/genetic/`) that evolves populations of adversarial chromosomes to stress-test pipeline boundaries across generations.

```
                  ┌───────────────────────────────┐
                  │ Seed Adversarial Chromosomes  │
                  └──────────────┬────────────────┘
                                 │
                                 ▼
                    ┌───────────────────────────┐
     ┌─────────────►│ Evaluate Pipeline Fitness │
     │              └────────────┬──────────────┘
     │                           │
     │       Fitness Breakdown:  │
     │       • 0.00 = Caught at Layer 1 Triage
     │       • 0.50 = Caught at Posological AST
     │       • 0.75 = Caught at Verification Gate
     │       • 1.00 = CRITICAL BREACH (Escape)
     │                           │
     │                           ▼
     │              ┌───────────────────────────┐
     │              │   Tournament Selection    │
     │              └────────────┬──────────────┘
     │                           │
     │                           ▼
     │              ┌───────────────────────────┐
     └──────────────┤  Crossover & Mutations    │
                    │  (Dosage, Units, Spacing, │
                    │   Zero-Width, Homoglyphs) │
                    └───────────────────────────┘
```

### Empirical Genetic Benchmark (4 Generations, 100 Evaluations)

```bash
Generations Run: 4
Total Adversarial Evaluations: 100
Escaped Count: 0
Escape Rate: 0.00%
Resilience Score: 100.00%
Stage Breakdown:
  • Intercepted at Layer 1 Triage: 42
  • Intercepted at Posological AST Engine: 58
  • Escaped Pipeline Breaches: 0
```

---

## 5. Technology Stack & Orchestration

* **Orchestration**: LangGraph StateGraph (`src/pipeline/langgraph_pipeline.py`) with cyclic critique/repair loops and conditional routing.
* **Observability & Tracing**: OpenTelemetry SDK + Langfuse integration (`src/telemetry/tracer.py`) logging stage latencies, token usage, and LLM evaluation scores.
* **Posological AST Engine**: Deterministic Regex AST parser with unit normalization (`mcg` -> `mg`, `g` -> `mg`) and cumulative posology tracking.
* **Literature Grounding**: Official NCBI Entrez E-Utilities (`httpx` async client) with fallback to curated clinical abstracts.
* **Persistence**: SQLite append-only audit ledger with WAL mode, busy timeout, and thread locks (`src/persistence/db.py`).
* **API & Visual UI**: FastAPI serving REST endpoints and an editorial dark-mode dashboard conforming to `/hub-design` invariants.
* **Containerization**: Multi-stage, non-root Docker build (`USER 10001:10001`) with container healthcheck.

---

## 6. Quickstart & Local Installation

### Prerequisites
* Python 3.11+
* Docker & Docker Compose (optional)

### 1. Clone & Setup Virtual Environment
```bash
git clone https://github.com/Ali-Ch-001/looksmaxxing_guide.git
cd looksmaxxing_guide

python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -e .
pip install -r requirements.txt # or install dependencies
```

### 2. Configure Environment Variables
```bash
cp .env.example .env
```

### 3. Run Test Suite & Negative Evaluations
```bash
# Runs all 96 unit, integration, and 50 adversarial negative test cases
pytest -v --cov=src --cov-report=term-missing
```

### 4. Launch the Web Application & API
```bash
uvicorn src.server:app --host 0.0.0.0 --port 8000 --reload
```
Open your browser at:
* **Interactive Web Platform**: [http://localhost:8000](http://localhost:8000)
* **Interactive API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Container Healthcheck**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 7. One-Click Docker Deployment

```bash
# Multi-stage container build and non-root execution
docker-compose up -d --build

# Verify container health
docker-compose ps
curl http://localhost:8000/health
```

---

## 8. CLI Usage Examples

```bash
# 1. Generate verified clinical guide with Schema.org JSON-LD
python -m src.cli --topic "oral minoxidil" --output-dir dist/content

# 2. Test Banned Topic (triggers Crisis Notice routing)
python -m src.cli --topic "bone smashing jawline" --output-dir dist/content
```

---

## 10. Completed Strategic Roadmap: Autonomous Clinical AI Architecture

All four strategic roadmap capabilities have been implemented and verified across the test suite:

### 1. Hybrid Deterministic / Semantic Verifier (`src/verification/hybrid_critic.py`)
* Couples the un-bypassable posological AST engine with an LLM Critic Agent using Chain-of-Thought (CoT) reasoning.
* Detects complex drug-drug interaction nuances (e.g. retinoids without photoprotection, systemic vasodilators lacking cardiovascular baselines, Category X teratogenicity warnings) that regex cannot capture.

### 2. Targeted Programmatic Repair Loop with AST Diff Feedback (`src/verification/gate_engine.py`)
* Replaces naive string replacement by feeding structured AST violation diffs directly back into the repair engine.
* Surgically rewrites only non-compliant protocol statements to safe conservative ranges while preserving compliant surrounding prose.

### 3. Dynamic MeSH Query Expansion (`src/retrieval/mesh_expander.py`)
* Autonomously refines low-density search queries by mapping colloquial consumer phrases (`"hair thinning"`, `"acne"`, `"mewing"`) to official National Library of Medicine Medical Subject Headings (MeSH).
* Formulates expanded boolean syntax (`("Alopecia"[Mesh] OR "Hypotrichosis"[Mesh])`) to retrieve authoritative clinical trials dynamically.

### 4. Cache Invalidation on Guideline Updates (`src/persistence/state_graph.py`)
* Computes a deterministic SHA256 fingerprint of `CLINICAL_DICTIONARY` posological ceilings and embeds it into every SQLite idempotency key (`SHA256(topic:version:fingerprint)`).
* Any tightening or revision of medical dosage thresholds instantly invalidates stale checkpoints, permanently preventing cache poisoning.

---

## 11. License & Safety Disclaimer

This project is licensed under the MIT License.

**Clinical Disclaimer:** Content generated by this platform is designed strictly for harm reduction, patient education, and research synthesis. It does not constitute formal medical diagnosis or individualized prescription. All systemic prescription therapies (e.g., oral minoxidil, finasteride, isotretinoin) require baseline cardiovascular and hepatic laboratory evaluation by a licensed physician.
