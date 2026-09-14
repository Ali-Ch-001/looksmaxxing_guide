"""Headless CMS & Static Site Generator (SSG) Exporter.

Transforms verified PipelineState into frontmatter Markdown with injected
Schema.org JSON-LD scripts, consensus tags, and citation matrices.
"""

import json
import os
from typing import Optional, Dict, Any
from src.schemas.pipeline_state import PipelineState


class CMSExporter:
    """Exports clinical articles for modern static site generators and headless CMS."""

    @staticmethod
    def render_markdown(state: PipelineState) -> str:
        if state.is_crisis_routed and state.crisis_payload:
            # Render Harm-Reduction / Crisis Notice Page
            payload = state.crisis_payload
            resources = payload.get("crisis_resources", {})
            return f"""---
title: "Clinical Harm-Reduction Advisory: {state.raw_topic.title()}"
slug: "{state.raw_topic.lower().replace(' ', '-')}-advisory"
category: "harm_reduction"
risk_level: "PROHIBITED_PRACTICE"
status: "crisis_routed"
---

# Clinical Harm-Reduction Advisory: {state.raw_topic.title()}

> **WARNING:** This subject involves practices identified by dermatological and maxillofacial surgical literature as high-risk, self-injurious, or medically hazardous. Automated instructional guides are strictly barred.

## Mechanism of Injury & Clinical Hazards
{payload.get("harm_reduction_warning", "This practice causes irreversible musculoskeletal trauma or chemical injury.")}

## Clinical Helplines & Evidence Resources
* **Emergency Support:** {resources.get("emergency", "Call 988 (USA) or 111 (UK) if in distress.")}
* **Body Dysmorphic Support:** [{resources.get("body_dysmorphia", {}).get("organization", "BDD Foundation")}]({resources.get("body_dysmorphia", {}).get("url", "https://bddfoundation.org")})
"""

        if not state.draft:
            raise ValueError("Cannot export CMS markdown without an article draft.")

        draft = state.draft
        json_ld_str = json.dumps(state.output_json_ld, indent=2) if state.output_json_ld else "{}"

        # Build protocol list
        protocol_md = "\n".join(f"{idx+1}. {step}" for idx, step in enumerate(draft.actionable_protocol))

        # Build contraindications list
        contraindications_md = "\n".join(f"- ⚠️ **{item}**" for item in draft.contraindications)

        # Build FAQ list
        faq_md = "\n\n".join(
            f"### Q: {faq.question}\n**A:** {faq.answer}"
            for faq in draft.structured_faq
        )

        # Build citations list
        citations_md = "\n".join(f"- [{c}](https://pubmed.ncbi.nlm.nih.gov/{c.replace('PMID:', '')}/)" for c in draft.citations)

        return f"""---
title: "{draft.title}"
slug: "{draft.slug}"
target_keyword: "{draft.target_kw}"
discipline: "{state.discipline_namespace}"
risk_category: "{state.risk_category}"
audience: "{draft.audience_demographic}"
audit_passed: true
schema_org: "MedicalWebPage, FAQPage"
---

# {draft.title}

<div class="evidence-badge">
  <strong>Clinical Evidence Status:</strong> Verified Against Peer-Reviewed Literature
</div>

## Scientific Consensus & Summary
{draft.scientific_summary}

## Actionable Protocol & Dosage Ceilings
{protocol_md}

## Absolute Medical Contraindications
{contraindications_md}

## Frequently Asked Questions (GEO/Answer Engine Optimized)
{faq_md}

## Peer-Reviewed Clinical Citations
{citations_md}

<script type="application/ld+json">
{json_ld_str}
</script>
"""

    @classmethod
    def export_to_file(cls, state: PipelineState, output_dir: str = "dist/content") -> str:
        os.makedirs(output_dir, exist_ok=True)
        md_content = cls.render_markdown(state)
        state.output_cms_markdown = md_content

        slug = state.draft.slug if state.draft else state.raw_topic.lower().replace(" ", "-")
        file_path = os.path.join(output_dir, f"{slug}.md")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return file_path
