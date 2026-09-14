"""Unit tests for Context Splitting and Discipline Namespace Isolation."""

import pytest
from src.retrieval.context_splitter import ContextSplitter, DisciplineNamespace


def test_namespace_resolution():
    assert ContextSplitter.resolve_namespace("tretinoin cream") == DisciplineNamespace.DERMATOLOGY_TRICHOLOGY
    assert ContextSplitter.resolve_namespace("oral minoxidil") == DisciplineNamespace.DERMATOLOGY_TRICHOLOGY
    assert ContextSplitter.resolve_namespace("mewing palate") == DisciplineNamespace.ORTHODONTICS
    assert ContextSplitter.resolve_namespace("severe hypertension") == DisciplineNamespace.CARDIOLOGY_HYPERTENSION
    assert ContextSplitter.resolve_namespace("neck hypertrophy workout") == DisciplineNamespace.FITNESS_NUTRITION
    assert ContextSplitter.resolve_namespace("unknown random query") == DisciplineNamespace.GENERAL


def test_query_sanitization():
    sanitized = ContextSplitter.sanitize_query("minoxidil hair loss", DisciplineNamespace.DERMATOLOGY_TRICHOLOGY)
    assert "NOT" in sanitized
    assert "hypertensive emergency" in sanitized.lower()


def test_document_filtering_excludes_cardiology():
    docs = [
        {
            "id": "PMID:1",
            "title": "Minoxidil for Hair Growth",
            "snippet": "Dermatological study of low dose.",
            "discipline_namespace": DisciplineNamespace.DERMATOLOGY_TRICHOLOGY
        },
        {
            "id": "PMID:2",
            "title": "Minoxidil in Refractory Hypertension Emergency",
            "snippet": "Cardiovascular blood pressure control with 40mg daily.",
            "discipline_namespace": DisciplineNamespace.CARDIOLOGY_HYPERTENSION
        }
    ]
    filtered = ContextSplitter.filter_documents_for_namespace(docs, DisciplineNamespace.DERMATOLOGY_TRICHOLOGY)
    assert len(filtered) == 1
    assert filtered[0]["id"] == "PMID:1"
