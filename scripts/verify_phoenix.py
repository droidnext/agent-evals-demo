#!/usr/bin/env python3
"""Verify Phoenix tracing is properly configured and working."""

import sys
from pathlib import Path

# Add agents to path
sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))

print("=" * 60)
print("Phoenix Tracing Verification")
print("=" * 60)
print()

# Import config for Phoenix settings, tracing_util for initialization & verification
from cruise_booking import config
from cruise_booking import tracing_util
tracing_util.initialize_tracing()

print()
print("📊 Configuration Status:")
print(f"  PHOENIX_ENABLED: {config.PHOENIX_ENABLED}")
print(f"  PHOENIX_API_KEY: {'SET ✅' if config.PHOENIX_API_KEY else 'NOT SET ❌'}")
print(f"  PHOENIX_ENDPOINT: {config.PHOENIX_COLLECTOR_ENDPOINT}")
print(f"  PHOENIX_PROJECT: {config.PHOENIX_PROJECT_NAME}")
print()

# Verify instrumentation
if hasattr(tracing_util, 'verify_phoenix_instrumentation'):
    print("🔍 Instrumentation Status:")
    status = tracing_util.verify_phoenix_instrumentation()
    
    if status.get("enabled"):
        print("  ✅ Phoenix tracing is ACTIVE")
        print(f"  📡 Endpoint: {status.get('endpoint')}")
        print(f"  📦 Project: {status.get('project')}")
        print(f"  🔌 Instrumented: {', '.join(status.get('instrumentation', []))}")
    else:
        print(f"  ❌ Phoenix tracing is INACTIVE")
        print(f"  ❓ Reason: {status.get('reason')}")
        sys.exit(1)
else:
    print("  ⚠️  Verification function not available")

print()

# Check OpenTelemetry setup
try:
    from opentelemetry import trace as trace_api
    from openinference.instrumentation.litellm import LiteLLMInstrumentor
    
    print("🔌 Instrumentation Details:")
    
    # Check tracer provider
    tracer_provider = trace_api.get_tracer_provider()
    print(f"  Tracer Provider: {type(tracer_provider).__name__}")
    
    # Check LiteLLM instrumentation
    litellm_instrumentor = LiteLLMInstrumentor()
    is_instrumented = litellm_instrumentor.is_instrumented_by_opentelemetry
    print(f"  LiteLLM Instrumented: {'✅ YES' if is_instrumented else '❌ NO'}")
    
    # Try OpenAI instrumentation
    try:
        from openinference.instrumentation.openai import OpenAIInstrumentor
        openai_instrumentor = OpenAIInstrumentor()
        openai_instrumented = openai_instrumentor.is_instrumented_by_opentelemetry
        print(f"  OpenAI Instrumented: {'✅ YES' if openai_instrumented else '❌ NO (optional)'}")
    except ImportError:
        print(f"  OpenAI Instrumented: ℹ️  Not available (optional)")
    
    print()
    print("✅ All checks passed!")
    print()
    print("📝 Next Steps:")
    print("  1. Send a query to your agent")
    print("  2. Check Phoenix UI for traces:")
    print(f"     {config.PHOENIX_COLLECTOR_ENDPOINT}")
    print("  3. Look for project: cruise-booking-agent")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("   Install with: uv pip install openinference-instrumentation-litellm")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 60)
