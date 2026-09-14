"""Unit tests for CMS Exporter."""

import os
import pytest
from src.deployment.cms_exporter import CMSExporter
from src.schemas.pipeline_state import PipelineState, ArticleDraft, FAQItem


def test_cms_exporter_file_creation(tmp_path):
    draft = ArticleDraft(
        title="Clinical Guide to Minoxidil",
        slug="clinical-minoxidil-guide",
        target_kw="minoxidil",
        scientific_summary="Evidence summary.",
        actionable_protocol=["Take 1.25 mg daily [PMID:33675122]."],
        contraindications=["Heart disease"],
        citations=["PMID:33675122"],
        structured_faq=[FAQItem(question="Is it safe?", answer="Yes at 1.25mg.")]
    )
    state = PipelineState(
        raw_topic="oral minoxidil",
        retrieved_papers=[{"id": "PMID:33675122"}],
        draft=draft,
        audit_passed=True
    )

    out_dir = str(tmp_path / "content")
    file_path = CMSExporter.export_to_file(state, output_dir=out_dir)

    assert os.path.exists(file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Clinical Guide to Minoxidil" in content
    assert "Take 1.25 mg daily" in content
    assert "PMID:33675122" in content
