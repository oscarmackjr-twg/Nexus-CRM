from __future__ import annotations


def setup_telemetry(app, settings=None) -> None:
    """Initialise OpenTelemetry tracing. No exporter configured yet — traces stay in-process."""
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        provider = TracerProvider()
        trace.set_tracer_provider(provider)
    except ImportError:
        pass


class _Counter:
    """Minimal Prometheus-compatible counter stub."""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self._value = 0

    def inc(self, amount: int = 1, **labels) -> None:
        self._value += amount

    def __call__(self, *args, **kwargs):
        return self


deal_created_counter = _Counter("deal_created_total", "Deals created")
deal_won_counter = _Counter("deal_won_total", "Deals won")
ai_query_counter = _Counter("ai_query_total", "AI query requests")
automation_run_counter = _Counter("automation_run_total", "Automation runs")
linkedin_import_counter = _Counter("linkedin_import_total", "LinkedIn imports")
