"""Phoenix tracing initialization and utilities."""

import socket
from contextlib import nullcontext
from urllib.parse import urlparse

from .config import (
    PHOENIX_API_KEY,
    PHOENIX_COLLECTOR_ENDPOINT,
    PHOENIX_ENABLED,
    PHOENIX_PROJECT_NAME,
    is_local_phoenix,
)


class NoOpTracer:
    """No-op tracer when Phoenix is not available."""
    def chain(self, func):
        return func
    def tool(self, func):
        return func
    def agent(self, func):
        return func
    def llm(self, func):
        return func
    def start_as_current_span(self, *args, **kwargs):
        return nullcontext()


_tracer_provider = None
tracer = NoOpTracer()
_initialized = False


def initialize_tracing():
    """Initialize Phoenix tracing. Safe to call multiple times (no-op after first)."""
    global _tracer_provider, tracer, _initialized

    if _initialized:
        return

    _initialized = True

    if not PHOENIX_ENABLED:
        print("ℹ️  Phoenix tracing disabled")
        return

    try:
        from phoenix.otel import register

        print("🔄 Initializing Phoenix tracing...")

        if is_local_phoenix:
            # Local Docker Phoenix: gRPC on port 4317, no auth needed.
            # Port 6006 is the UI only — traces must go via gRPC.
            _tracer_provider = register(
                project_name=PHOENIX_PROJECT_NAME,
                endpoint="http://localhost:4317",
                batch=True,
                auto_instrument=True,
                set_global_tracer_provider=False,
            )
        else:
            headers = {}
            if PHOENIX_API_KEY:
                headers["api_key"] = PHOENIX_API_KEY
            _tracer_provider = register(
                project_name=PHOENIX_PROJECT_NAME,
                endpoint=PHOENIX_COLLECTOR_ENDPOINT,
                headers=headers,
                batch=True,
                auto_instrument=True,
                set_global_tracer_provider=False,
            )

        # BaseInstrumentor.instrument is an instance method, so we must instantiate
        # the instrumentors instead of calling instrument() on the class itself.
        from openinference.instrumentation.litellm import LiteLLMInstrumentor
        from openinference.instrumentation.google_adk import GoogleADKInstrumentor
        from openinference.instrumentation.openai import OpenAIInstrumentor
        from openinference.instrumentation.vertexai import VertexAIInstrumentor

        LiteLLMInstrumentor().instrument(tracer_provider=_tracer_provider)
        GoogleADKInstrumentor().instrument(tracer_provider=_tracer_provider)
        OpenAIInstrumentor().instrument(tracer_provider=_tracer_provider)
        VertexAIInstrumentor().instrument(tracer_provider=_tracer_provider)

        tracer = _tracer_provider.get_tracer(__name__)

        try:
            from src.utils import phoenix_tracer
            phoenix_tracer.set_tracer(tracer)
        except ImportError:
            pass

        collector = "http://localhost:4317" if is_local_phoenix else PHOENIX_COLLECTOR_ENDPOINT
        reachable = _check_endpoint_reachable(collector)

        if reachable:
            print(f"✅ Phoenix tracing initialized — collector is reachable")
        else:
            print(f"⚠️  Phoenix tracing configured but collector is NOT reachable")
            print(f"   Traces will be lost until the collector is available.")

        print(f"   Collector: {collector}")
        print(f"   Project: {PHOENIX_PROJECT_NAME}")
        print(f"   Batch processing: ✅")
        print(f"   Auto-instrumentation: ✅")

    except ImportError as e:
        print(f"⚠️  Phoenix packages not installed: {e}")
        print("   Install with: uv pip install arize-phoenix")
    except Exception as e:
        print(f"⚠️  Phoenix initialization failed: {e}")
        import traceback
        traceback.print_exc()
        tracer = NoOpTracer()


def _check_endpoint_reachable(endpoint: str, timeout: float = 2.0) -> bool:
    """TCP connect check to see if the collector is actually listening."""
    try:
        parsed = urlparse(endpoint)
        host = parsed.hostname or "localhost"
        # gRPC default 4317, HTTP default from scheme
        port = parsed.port or (443 if parsed.scheme == "https" else 4317 if is_local_phoenix else 80)
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def verify_phoenix_instrumentation():
    """Verify that Phoenix instrumentation is active."""
    if not PHOENIX_ENABLED:
        return {"enabled": False, "reason": "Phoenix not enabled"}

    if _tracer_provider is None:
        return {"enabled": False, "reason": "Tracer provider not initialized"}

    try:
        from opentelemetry import trace as trace_api
        tracer_provider = trace_api.get_tracer_provider()

        if tracer_provider and hasattr(tracer_provider, '_active_span_processor'):
            return {
                "enabled": True,
                "endpoint": PHOENIX_COLLECTOR_ENDPOINT,
                "project": PHOENIX_PROJECT_NAME,
                "auto_instrumentation": True,
                "batch_processing": True,
                "status": "active"
            }
        else:
            return {"enabled": False, "reason": "Tracer provider not properly configured"}
    except Exception as e:
        return {"enabled": False, "reason": f"Verification error: {e}"}


def get_tracer():
    """
    Get the Phoenix tracer for manual instrumentation.

    Use this tracer with decorators like @tracer.tool, @tracer.chain, etc.
    Returns a NoOpTracer if Phoenix is disabled or not yet initialized.

    Example:
        from .tracing_util import get_tracer

        tracer = get_tracer()
        @tracer.tool
        def my_function():
            pass
    """
    return tracer
