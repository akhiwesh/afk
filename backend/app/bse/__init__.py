"""
Business Science Engine (BSE) — deterministic diagnostic operating system.

Public entry point: DiagnosticPipeline.run()
"""
from backend.app.bse.orchestrator import DiagnosticPipeline
from backend.app.bse.version import ENGINE_VERSION

__all__ = ["DiagnosticPipeline", "ENGINE_VERSION"]