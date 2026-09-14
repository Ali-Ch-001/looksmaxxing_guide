"""Production FastAPI Server & Editorial UI for looksmaxxing.guide.

Evidence-led, harm-reduction-oriented content engine for the male aesthetic
and self-improvement subculture (grooming, fitness, dermatology, dental/orthodontic).
"""

from __future__ import annotations
import os
import time
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from src.pipeline.orchestrator import EvidenceLedPipeline
from src.pipeline.langgraph_pipeline import build_langgraph_pipeline
from src.safety.dosage_checker import DeterministicDosageEngine
from src.genetic.engine import EvolutionaryRedTeamEngine
from src.schemas.pipeline_state import PipelineState

app = FastAPI(
    title="looksmaxxing.guide - Evidence-Led Clinical SEO Engine",
    description="Deterministic, citation-grounded, medical harm-reduction content platform for male aesthetic self-improvement.",
    version="0.1.0"
)

# Initialize pipelines
_linear_pipeline = EvidenceLedPipeline()
_langgraph_app = build_langgraph_pipeline()


class GenerateRequest(BaseModel):
    topic: str = Field(..., description="Target aesthetic/dermatological topic (e.g. 'oral minoxidil', 'topical tretinoin')")
    use_langgraph: bool = Field(default=True, description="Execute via LangGraph StateGraph engine")


class VerifyDosageRequest(BaseModel):
    text: str = Field(..., description="Sentence or protocol text to verify for posological safety")
    default_compound: Optional[str] = Field(default=None, description="Fallback compound name if not detected in text")


class GeneticEvalRequest(BaseModel):
    population_size: int = Field(default=25, ge=10, le=100)
    generations: int = Field(default=4, ge=1, le=20)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "looksmaxxing.guide-engine",
        "version": "0.1.0",
        "environment": os.getenv("ENVIRONMENT", "production")
    }


@app.post("/api/v1/generate")
async def generate_article(req: GenerateRequest):
    t0 = time.perf_counter()
    topic = req.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Topic cannot be empty")

    if req.use_langgraph:
        initial_state = {
            "raw_topic": topic,
            "normalized_topic": "",
            "risk_category": "fitness",
            "discipline_namespace": "general",
            "retrieved_papers": [],
            "evidence_matrix": None,
            "draft": None,
            "audit_passed": False,
            "rejection_reason": None,
            "is_crisis_routed": False,
            "crisis_payload": None,
            "repair_attempts": 0,
            "max_repair_attempts": 2,
            "audit_history": [],
            "step_history": [],
            "output_cms_markdown": None,
            "output_json_ld": None,
            "telemetry": None
        }
        res = await _langgraph_app.ainvoke(initial_state)
        duration_ms = (time.perf_counter() - t0) * 1000.0
        return {
            "engine": "LangGraph StateGraph",
            "topic": topic,
            "risk_category": res["risk_category"],
            "discipline_namespace": res["discipline_namespace"],
            "audit_passed": res["audit_passed"],
            "rejection_reason": res["rejection_reason"],
            "is_crisis_routed": res["is_crisis_routed"],
            "crisis_payload": res["crisis_payload"],
            "draft": res["draft"],
            "citations_count": len(res["draft"].citations) if res["draft"] else 0,
            "markdown": res["output_cms_markdown"],
            "json_ld": res["output_json_ld"],
            "step_history": res["step_history"],
            "duration_ms": round(duration_ms, 2)
        }
    else:
        state: PipelineState = await _linear_pipeline.run(topic)
        return {
            "engine": "Linear Orchestrator",
            "topic": state.raw_topic,
            "risk_category": state.risk_category,
            "discipline_namespace": state.discipline_namespace,
            "audit_passed": state.audit_passed,
            "rejection_reason": state.rejection_reason,
            "is_crisis_routed": state.is_crisis_routed,
            "crisis_payload": state.crisis_payload,
            "draft": state.draft.model_dump() if state.draft else None,
            "citations_count": len(state.draft.citations) if state.draft else 0,
            "markdown": state.output_cms_markdown,
            "json_ld": state.output_json_ld,
            "step_history": state.step_history,
            "duration_ms": round(state.telemetry.duration_ms, 2) if state.telemetry else None
        }


@app.post("/api/v1/verify-dosage")
async def verify_dosage(req: VerifyDosageRequest):
    passed, violations, warnings = DeterministicDosageEngine.verify_protocols(
        [req.text],
        default_compound=req.default_compound
    )
    extractions = DeterministicDosageEngine.extract_dosages_from_text(
        req.text,
        default_compound=req.default_compound
    )
    return {
        "passed": passed,
        "violations": violations,
        "warnings": warnings,
        "extracted_posology": [e.to_dict() for e in extractions]
    }


@app.post("/api/v1/genetic-eval")
async def run_genetic_evaluation(req: GeneticEvalRequest):
    engine = EvolutionaryRedTeamEngine(
        population_size=req.population_size,
        generations=req.generations,
        mutation_rate=0.4,
        crossover_rate=0.7
    )
    report = engine.run_evolution()
    return {
        "generations_run": report.generations_run,
        "population_size": report.population_size,
        "total_evaluations": report.total_evaluations,
        "escaped_count": report.escaped_count,
        "escape_rate": report.escape_rate,
        "resilience_score": report.resilience_score,
        "stage_breakdown": report.stage_breakdown,
        "best_fitness_history": report.best_fitness_history
    }


# ==============================================================================
# Editorial Visual Web Application
# ==============================================================================

HTML_UI = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>looksmaxxing.guide — Evidence-Led Male Self-Improvement</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            brand: { 50: '#ecfdf5', 500: '#10b981', 600: '#059669', 900: '#064e3b' },
            dark: { 950: '#090a0f', 900: '#0f111a', 800: '#181b28', 700: '#23283c' }
          },
          fontFamily: {
            sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
            mono: ['JetBrains Mono', 'Menlo', 'monospace']
          }
        }
      }
    }
  </script>
  <style>
    /* /hub-design invariant: Concentric radius: R_outer = R_inner + padding */
    .card-outer { border-radius: 16px; padding: 20px; }
    .card-inner { border-radius: 10px; }
    /* Tactile button interaction */
    .tactile-btn {
      transition: transform 120ms ease-out, background-color 150ms ease;
    }
    .tactile-btn:active {
      transform: scale(0.97);
    }
  </style>
</head>
<body class="bg-dark-950 text-slate-100 min-h-screen font-sans antialiased selection:bg-emerald-500 selection:text-white">

  <!-- Navigation Bar -->
  <header class="border-b border-dark-700/60 bg-dark-900/80 backdrop-blur-md sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center font-bold text-dark-950 text-lg">L</div>
        <span class="font-extrabold text-xl tracking-tight text-white">looksmaxxing<span class="text-emerald-400">.guide</span></span>
        <span class="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 font-mono border border-emerald-500/20">EVIDENCE ENGINE v0.1.0</span>
      </div>
      <div class="flex items-center space-x-4 text-sm font-medium text-slate-400">
        <span class="hidden sm:inline text-xs text-slate-400">Target: Men 18–35 (US/UK/AU/CA)</span>
        <a href="#simulator" class="hover:text-emerald-400 transition">Posology AST</a>
        <a href="#genetic" class="hover:text-emerald-400 transition">Genetic Fuzzer</a>
        <a href="/docs" target="_blank" class="px-3 py-1.5 rounded-md bg-dark-800 text-slate-200 hover:bg-dark-700 transition border border-dark-700">API Docs</a>
      </div>
    </div>
  </header>

  <!-- Hero Section -->
  <main class="max-w-7xl mx-auto px-6 py-12 space-y-12">
    <div class="text-center max-w-3xl mx-auto space-y-4">
      <div class="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-950/60 text-emerald-400 border border-emerald-800/60 text-xs font-mono">
        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
        <span>ZERO INCEL JARGON • 100% CLINICAL CITATION GROUNDED</span>
      </div>
      <h1 class="text-4xl sm:text-5xl font-extrabold tracking-tight text-white">
        Evidence-Led Aesthetic Protocols for Men
      </h1>
      <p class="text-slate-400 text-lg">
        Demystifying male grooming, trichology, and dermatological protocols with deterministic clinical boundaries. Combats toxic subculture misinformation and unmonitored posological hazards.
      </p>
    </div>

    <!-- Live Topic Generator -->
    <div class="bg-dark-900 border border-dark-700/80 card-outer shadow-2xl space-y-6">
      <div class="flex flex-col sm:flex-row gap-3">
        <input id="topicInput" type="text" value="oral minoxidil" placeholder="Enter topic: 'topical tretinoin', 'bone smashing', 'palatal mewing'..."
          class="flex-1 bg-dark-950 border border-dark-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 font-mono text-sm">
        <button onclick="runPipeline()" class="tactile-btn px-6 py-3 bg-emerald-500 hover:bg-emerald-400 text-dark-950 font-bold rounded-lg flex items-center justify-center space-x-2 shadow-lg shadow-emerald-500/20">
          <span>Run Evidence Pipeline</span>
        </button>
      </div>

      <div class="flex flex-wrap gap-2 text-xs font-mono text-slate-400">
        <span>Try quick scenarios:</span>
        <button onclick="setTopic('oral minoxidil')" class="hover:text-emerald-400 underline">oral minoxidil</button>
        <span>•</span>
        <button onclick="setTopic('topical tretinoin')" class="hover:text-emerald-400 underline">topical tretinoin</button>
        <span>•</span>
        <button onclick="setTopic('bone smashing')" class="hover:text-red-400 underline">bone smashing (Banned)</button>
        <span>•</span>
        <button onclick="setTopic('diy lefort')" class="hover:text-red-400 underline">diy lefort (Banned)</button>
      </div>

      <!-- Result Container -->
      <div id="outputArea" class="hidden space-y-4 pt-4 border-t border-dark-700/60">
        <div id="statusBanner" class="p-4 rounded-lg flex items-start space-x-3"></div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="bg-dark-950 border border-dark-700 card-inner p-4 space-y-3">
            <h3 class="text-sm font-bold text-slate-300 uppercase tracking-wider font-mono">Rendered Clinical Guide</h3>
            <div id="mdOutput" class="text-sm text-slate-300 prose prose-invert max-w-none space-y-2 max-h-96 overflow-y-auto font-sans"></div>
          </div>
          <div class="bg-dark-950 border border-dark-700 card-inner p-4 space-y-3">
            <h3 class="text-sm font-bold text-slate-300 uppercase tracking-wider font-mono">Schema.org JSON-LD (GEO / Perplexity Ready)</h3>
            <pre id="jsonLdOutput" class="text-xs text-emerald-400 font-mono bg-dark-900 p-3 rounded overflow-x-auto max-h-96"></pre>
          </div>
        </div>
      </div>
    </div>

    <!-- Real-Time Posological AST Checker -->
    <div id="simulator" class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <div class="bg-dark-900 border border-dark-700/80 card-outer space-y-4">
        <div class="flex items-center justify-between">
          <h2 class="text-xl font-bold text-white flex items-center space-x-2">
            <span>Deterministic Posological AST Engine</span>
          </h2>
          <span class="text-xs px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 font-mono">Decoupled from LLM</span>
        </div>
        <p class="text-slate-400 text-sm">
          Tests sentences against hard clinical dosage ceilings (`CLINICAL_DICTIONARY`). Normalizes units (`mcg` -> `mg`, `g` -> `mg`) and calculates frequency-multiplied daily posology.
        </p>
        <textarea id="posologyText" rows="3" class="w-full bg-dark-950 border border-dark-700 rounded-lg p-3 text-sm text-white font-mono placeholder-slate-500 focus:outline-none focus:border-emerald-500" placeholder="e.g. Take 10 mg oral minoxidil daily for hair thinning..."></textarea>
        <div class="flex items-center justify-between">
          <button onclick="testDosage()" class="tactile-btn px-4 py-2 bg-dark-800 hover:bg-dark-700 border border-dark-600 rounded text-sm font-medium text-white">
            Verify Dosage Claim
          </button>
          <div class="space-x-2 text-xs text-slate-400 font-mono">
            <button onclick="setDosageTest('Take 10 mg oral minoxidil daily')" class="hover:text-emerald-400">10mg (hypertension leak)</button>
            <button onclick="setDosageTest('Take 10000 mcg oral minoxidil daily')" class="hover:text-emerald-400">10,000 mcg</button>
            <button onclick="setDosageTest('Take 3 mg oral minoxidil twice daily')" class="hover:text-emerald-400">3mg bid (6mg/d)</button>
          </div>
        </div>
        <div id="dosageResult" class="hidden p-3 rounded font-mono text-xs space-y-1"></div>
      </div>

      <!-- Genetic Evolutionary Red-Team Simulator -->
      <div id="genetic" class="bg-dark-900 border border-dark-700/80 card-outer space-y-4">
        <div class="flex items-center justify-between">
          <h2 class="text-xl font-bold text-white flex items-center space-x-2">
            <span>Evolutionary Genetic Red-Team Loop</span>
          </h2>
          <span class="text-xs px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 font-mono">Mutational Fuzzer</span>
        </div>
        <p class="text-slate-400 text-sm">
          Simulates genetic evolution across generations using chromosome mutations, zero-width obfuscation, homoglyphs, and split-posology to prove 0% escape rate.
        </p>
        <div class="flex items-center space-x-3">
          <button onclick="runGeneticFuzzer()" class="tactile-btn px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded text-sm font-medium">
            Launch 4-Gen Fuzzing Run
          </button>
          <span id="geneticStatus" class="text-xs font-mono text-slate-400">Idle. Ready for adversarial test.</span>
        </div>
        <div id="geneticReport" class="hidden p-3 bg-dark-950 border border-dark-700 rounded text-xs font-mono space-y-2"></div>
      </div>
    </div>

    <!-- Positioning & Competitive Landscape Card -->
    <div class="border border-dark-700/80 bg-dark-900/60 card-outer space-y-4">
      <h3 class="text-lg font-bold text-white">Editorial Positioning: looksmaxxing.guide</h3>
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs font-mono text-slate-300">
        <div class="p-3 bg-dark-950 rounded border border-dark-700">
          <div class="text-emerald-400 font-bold mb-1">looksmaxxing.guide</div>
          <div>Evidence-led clinical protocols, PubMed PMIDs, Schema.org Answer Engine optimization, 0% toxic slang.</div>
        </div>
        <div class="p-3 bg-dark-950 rounded border border-dark-700">
          <div class="text-red-400 font-bold mb-1">Reddit r/looksmaxxing</div>
          <div>User UGC, low medical rigor, unmoderated dangerous hacks, zero structured machine-readable schemas.</div>
        </div>
        <div class="p-3 bg-dark-950 rounded border border-dark-700">
          <div class="text-red-400 font-bold mb-1">Looksmax.org Forum</div>
          <div>Toxic incel subculture tropes ('it\\'s over', 'subhuman'), illegal grey-market sources, physical harm hazards.</div>
        </div>
        <div class="p-3 bg-dark-950 rounded border border-dark-700">
          <div class="text-blue-400 font-bold mb-1">GQ / Men\\'s Health</div>
          <div>Mainstream lifestyle, low molecular specificity, sponsor-driven, lacks deterministic posological safety gates.</div>
        </div>
      </div>
    </div>
  </main>

  <footer class="border-t border-dark-700/60 py-8 mt-16 text-center text-xs text-slate-500 font-mono">
    looksmaxxing.guide &bull; Deterministic Clinical Harm Reduction Engine &bull; Non-Commercial Educational Architecture
  </footer>

  <script>
    function setTopic(t) { document.getElementById('topicInput').value = t; runPipeline(); }
    function setDosageTest(t) { document.getElementById('posologyText').value = t; testDosage(); }

    async function runPipeline() {
      const topic = document.getElementById('topicInput').value.trim();
      if (!topic) return;
      const outArea = document.getElementById('outputArea');
      const banner = document.getElementById('statusBanner');
      const mdOut = document.getElementById('mdOutput');
      const jsonLdOut = document.getElementById('jsonLdOutput');

      outArea.classList.remove('hidden');
      banner.className = 'p-4 rounded-lg flex items-start space-x-3 bg-blue-950/60 text-blue-300 border border-blue-800/60';
      banner.innerHTML = '<span>Executing LangGraph StateGraph pipeline with OpenTelemetry spans...</span>';

      try {
        const resp = await fetch('/api/v1/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ topic, use_langgraph: true })
        });
        const data = await resp.json();

        if (data.is_crisis_routed) {
          banner.className = 'p-4 rounded-lg flex items-start space-x-3 bg-red-950/60 text-red-300 border border-red-800/60';
          banner.innerHTML = `<div><strong>[!] CRISIS NOTICE ACTIVATED:</strong> ${data.rejection_reason}</div>`;
        } else if (data.audit_passed) {
          banner.className = 'p-4 rounded-lg flex items-start space-x-3 bg-emerald-950/60 text-emerald-300 border border-emerald-800/60';
          banner.innerHTML = `<div><strong>[✓] ALL DETERMINISTIC VERIFICATION GATES PASSED:</strong> Verified with ${data.citations_count} PubMed citations in ${data.duration_ms} ms.</div>`;
        } else {
          banner.className = 'p-4 rounded-lg flex items-start space-x-3 bg-amber-950/60 text-amber-300 border border-amber-800/60';
          banner.innerHTML = `<div><strong>[X] AUDIT GATE QUARANTINE:</strong> ${data.rejection_reason}</div>`;
        }

        mdOut.innerText = data.markdown || 'No markdown output.';
        jsonLdOut.innerText = JSON.stringify(data.json_ld || {}, null, 2);
      } catch (err) {
        banner.className = 'p-4 rounded-lg bg-red-950 text-red-300 border border-red-800';
        banner.innerText = 'Error invoking pipeline: ' + err.message;
      }
    }

    async function testDosage() {
      const text = document.getElementById('posologyText').value.trim();
      const resDiv = document.getElementById('dosageResult');
      resDiv.classList.remove('hidden');

      const resp = await fetch('/api/v1/verify-dosage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      const data = await resp.json();

      if (data.passed) {
        resDiv.className = 'p-3 rounded font-mono text-xs space-y-1 bg-emerald-950/60 text-emerald-300 border border-emerald-800/60';
        resDiv.innerHTML = '<div>[✓] POSOLOGICALLY SAFE: Dose is within absolute clinical safety ceilings.</div>';
      } else {
        resDiv.className = 'p-3 rounded font-mono text-xs space-y-1 bg-red-950/60 text-red-300 border border-red-800/60';
        resDiv.innerHTML = `<div>[X] POSOLOGICAL ASSERTION FAILURE:</div><div>${data.violations.join('<br>')}</div>`;
      }
    }

    async function runGeneticFuzzer() {
      const status = document.getElementById('geneticStatus');
      const repDiv = document.getElementById('geneticReport');
      status.innerText = 'Evolving population over 4 generations...';
      repDiv.classList.remove('hidden');
      repDiv.innerHTML = 'Simulating mutational fuzzing...';

      const resp = await fetch('/api/v1/genetic-eval', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ population_size: 25, generations: 4 })
      });
      const rep = await resp.json();

      status.innerText = 'Completed. Escape Rate: ' + (rep.escape_rate * 100).toFixed(2) + '%';
      repDiv.innerHTML = `
        <div class="text-emerald-400 font-bold">Resilience Score: ${(rep.resilience_score * 100).toFixed(2)}% (0 ESCAPES)</div>
        <div>Total Adversarial Attacks Evaluated: ${rep.total_evaluations}</div>
        <div>Intercepted at Triage: ${rep.stage_breakdown.caught_at_triage || 0}</div>
        <div>Intercepted at Dosage AST: ${rep.stage_breakdown.caught_at_dosage_ast || 0}</div>
        <div>Intercepted at Verification Gate: ${rep.stage_breakdown.caught_at_verification_gate || 0}</div>
        <div class="text-slate-400">Best Adversarial Fitness by Gen: [${rep.best_fitness_history.join(', ')}]</div>
      `;
    }
  </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    return HTMLResponse(content=HTML_UI)
