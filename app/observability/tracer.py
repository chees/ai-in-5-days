"""Distributed Tracing with OpenTelemetry (Criteria 15).

Configures OpenTelemetry tracer provider, traces request flow across
agent reasoning steps, tool calls, and external cadastral API queries.
"""

from contextlib import contextmanager
from typing import Generator, Optional
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource


_tracer_initialized = False


def setup_tracing(service_name: str = "ai-in-5-days-architect") -> trace.Tracer:
    """Initializes and registers the OpenTelemetry TracerProvider."""
    global _tracer_initialized
    if not _tracer_initialized:
        resource = Resource.create({"service.name": service_name, "service.version": "0.1.0"})
        provider = TracerProvider(resource=resource)
        # In cloud environment, otel-gcp exporter can be added; ConsoleSpanExporter for dev/test
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        trace.set_tracer_provider(provider)
        _tracer_initialized = True
    return trace.get_tracer(service_name)


def get_tracer(service_name: str = "ai-in-5-days-architect") -> trace.Tracer:
    """Returns an OpenTelemetry tracer instance."""
    return trace.get_tracer(service_name)


@contextmanager
def span_context(name: str, attributes: Optional[dict] = None) -> Generator[trace.Span, None, None]:
    """Context manager for easily wrapping agent logic blocks in an OpenTelemetry span."""
    tracer = get_tracer()
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for k, v in attributes.items():
                span.set_attribute(k, str(v))
        yield span
