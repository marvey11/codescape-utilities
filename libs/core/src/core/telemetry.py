"""Shared telemetry context for Codescape worker applications."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import TYPE_CHECKING

from telemetry.client import TelemetryClient

if TYPE_CHECKING:
    from collections.abc import Generator


@contextmanager
def telemetry_context(
    service_name: str,
) -> Generator[TelemetryClient | None]:
    """Create a telemetry client when the orchestrator supplied a run ID."""
    if not os.getenv("SERVICE_RUN_ID"):
        yield None
        return

    api_url = os.getenv("TELEMETRY_API_URL", "http://localhost:8000")
    with TelemetryClient(api_url, service_name=service_name) as telemetry:
        yield telemetry
