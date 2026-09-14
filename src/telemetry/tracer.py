"""OpenTelemetry and Langfuse Observability Integration.

Provides unified distributed tracing, span instrumentation, and LLM audit scoring
across all agentic content pipeline stages and verification gates.
"""

from __future__ import annotations
import os
import logging
import functools
import time
from typing import Optional, Dict, Any, Callable
from contextlib import contextmanager

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)
from opentelemetry.trace import Status, StatusCode
from opentelemetry.sdk.resources import Resource

# Langfuse imports
try:
    from langfuse import Langfuse
    _HAS_LANGFUSE = True
except ImportError:
    _HAS_LANGFUSE = False

logger = logging.getLogger(__name__)

# Initialize OTel Tracer Provider
_RESOURCE = Resource.create({
    "service.name": os.getenv("OTEL_SERVICE_NAME", "looksmaxxing-evidence-engine"),
    "service.version": "0.1.0",
    "deployment.environment": os.getenv("ENVIRONMENT", "development")
})

_PROVIDER = TracerProvider(resource=_RESOURCE)
# Add ConsoleSpanExporter if in dev mode or OTLP endpoint not set
if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        _PROVIDER.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    except Exception as exc:
        logger.warning(f"Failed to initialize OTLP Span Exporter: {exc}")
else:
    # Silent in-memory / simple exporter to avoid stdout spam during tests
    pass

trace.set_tracer_provider(_PROVIDER)
_TRACER = trace.get_tracer("looksmaxxing-evidence-engine", "0.1.0")


class ObservabilityManager:
    """Manages unified tracing across OpenTelemetry and Langfuse."""

    def __init__(self):
        self.tracer = _TRACER
        self.langfuse: Optional[Any] = None

        if _HAS_LANGFUSE and os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
            try:
                self.langfuse = Langfuse(
                    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
                )
                logger.info("Langfuse observability client initialized.")
            except Exception as e:
                logger.warning(f"Could not connect to Langfuse: {e}")

    def get_tracer(self):
        return self.tracer

    @contextmanager
    def span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Context manager creating an OpenTelemetry span with telemetry attributes."""
        attrs = attributes or {}
        with self.tracer.start_as_current_span(name) as otel_span:
            for k, v in attrs.items():
                otel_span.set_attribute(str(k), str(v))
            try:
                yield otel_span
                otel_span.set_status(Status(StatusCode.OK))
            except Exception as exc:
                otel_span.record_exception(exc)
                otel_span.set_status(Status(StatusCode.ERROR, str(exc)))
                raise

    def log_score(self, trace_id: str, name: str, value: float, comment: Optional[str] = None):
        """Logs verification score to Langfuse for continuous LLM evaluation."""
        if self.langfuse:
            try:
                self.langfuse.score(
                    trace_id=trace_id,
                    name=name,
                    value=value,
                    comment=comment
                )
            except Exception as e:
                logger.warning(f"Failed to log score to Langfuse: {e}")


# Singleton instance
telemetry = ObservabilityManager()


def trace_stage(stage_name: str):
    """Decorator to trace an execution step with OpenTelemetry."""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with telemetry.span(f"pipeline.stage.{stage_name}", {"stage": stage_name}):
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with telemetry.span(f"pipeline.stage.{stage_name}", {"stage": stage_name}):
                return func(*args, **kwargs)

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator
