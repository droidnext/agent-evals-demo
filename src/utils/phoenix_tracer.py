"""Phoenix OTEL tracer - simple global access to Phoenix tracing.

This module provides a global tracer that can be imported from anywhere.
The tracer is automatically configured when Phoenix is available.
"""

# No-op tracer for when Phoenix is not available
class NoOpTracer:
    """No-op tracer that does nothing - used when Phoenix is disabled."""
    def chain(self, func):
        return func
    def tool(self, func):
        return func
    def agent(self, func):
        return func
    def llm(self, func):
        return func
    def retriever(self, func):
        return func
    def embedding(self, func):
        return func
    def start_as_current_span(self, *args, **kwargs):
        from contextlib import nullcontext
        return nullcontext()

# Get Phoenix tracer if available
tracer = NoOpTracer()  # Default to no-op

try:
    from phoenix.otel import get_current_tracer_provider
    tracer_provider = get_current_tracer_provider()
    if tracer_provider:
        # Get a tracer for manual instrumentation
        tracer = tracer_provider.get_tracer(__name__)
except Exception:
    pass  # Phoenix not available, use no-op tracer


def get_tracer():
    """
    Get the global Phoenix tracer.
    
    Returns:
        Tracer instance (either real Phoenix tracer or no-op)
    
    Example:
        from src.utils.phoenix_tracer import tracer
        
        @tracer.chain
        def my_workflow():
            pass
        
        @tracer.tool
        def my_tool():
            pass
    """
    return tracer


def set_tracer(new_tracer):
    """
    Set the global Phoenix tracer.
    
    Args:
        new_tracer: Tracer instance to set as the global tracer
    
    This allows other modules to configure the tracer after initialization.
    """
    global tracer
    tracer = new_tracer
