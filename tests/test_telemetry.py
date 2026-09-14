"""Unit tests for OpenTelemetry and Langfuse observability integration."""

import pytest
from src.telemetry.tracer import ObservabilityManager, telemetry, trace_stage


def test_span_context_manager():
    with telemetry.span("test_manual_span", {"test_attr": 42}) as span:
        assert span is not None


@pytest.mark.asyncio
async def test_trace_stage_decorator_async():
    @trace_stage("async_mock_stage")
    async def sample_async():
        return "async_done"

    res = await sample_async()
    assert res == "async_done"


def test_trace_stage_decorator_sync():
    @trace_stage("sync_mock_stage")
    def sample_sync():
        return "sync_done"

    res = sample_sync()
    assert res == "sync_done"


def test_log_score_fallback():
    # Should not throw even when Langfuse keys are absent in testing
    telemetry.log_score("trace-123", "safety_score", 1.0, "Testing fallback")
