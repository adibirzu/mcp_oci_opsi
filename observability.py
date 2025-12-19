from __future__ import annotations

import os
import socket
import typing as t
import warnings
from dataclasses import dataclass


@dataclass(frozen=True)
class OTelConfig:
    mode: str  # oci-apm | otlp-grpc | otlp-http | none
    endpoint: str | None
    headers: dict[str, str] | None
    enabled: bool


_OTEL_INITIALIZED = False


def _tracing_enabled() -> bool:
    return os.getenv("OTEL_TRACING_ENABLED", "true").lower() in ("1", "true", "yes", "on")


def _infer_mode(endpoint: str) -> str:
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        return "otlp-http"
    return "otlp-grpc"


def _get_otel_config() -> OTelConfig:
    if not _tracing_enabled():
        return OTelConfig(mode="none", endpoint=None, headers=None, enabled=False)

    oci_apm_endpoint = os.getenv("OCI_APM_ENDPOINT")
    oci_apm_key = os.getenv("OCI_APM_PRIVATE_DATA_KEY")
    if oci_apm_endpoint and oci_apm_key:
        return OTelConfig(
            mode="oci-apm",
            endpoint=oci_apm_endpoint,
            headers={"Authorization": f"dataKey {oci_apm_key}"},
            enabled=True,
        )

    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        return OTelConfig(
            mode=_infer_mode(otlp_endpoint),
            endpoint=otlp_endpoint,
            headers=_parse_headers(os.getenv("OTEL_EXPORTER_OTLP_HEADERS")),
            enabled=True,
        )

    if os.getenv("OTEL_DISABLE_LOCAL", "false").lower() in ("1", "true", "yes", "on"):
        return OTelConfig(mode="none", endpoint=None, headers=None, enabled=False)

    # Local collector fallback (gRPC)
    return OTelConfig(mode="otlp-grpc", endpoint="localhost:4317", headers=None, enabled=True)


def _parse_headers(raw: str | None) -> dict[str, str] | None:
    if not raw:
        return None
    parsed: dict[str, str] = {}
    for part in raw.split(","):
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        k = k.strip()
        v = v.strip()
        if k:
            parsed[k] = v
    return parsed or None


def _lazy_import_otel() -> tuple[bool, dict[str, t.Any]]:
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        return True, {
            "trace": trace,
            "Resource": Resource,
            "TracerProvider": TracerProvider,
            "BatchSpanProcessor": BatchSpanProcessor,
        }
    except Exception:
        return False, {}


def init_tracing(service_name: str) -> None:
    """
    Initialize OpenTelemetry tracing for the OPSI MCP server.

    Supports:
    - OCI APM via `OCI_APM_ENDPOINT` + `OCI_APM_PRIVATE_DATA_KEY` (OTLP/HTTP)
    - Generic OTLP endpoint via `OTEL_EXPORTER_OTLP_ENDPOINT` (HTTP or gRPC)
    - Local collector fallback `localhost:4317` unless `OTEL_DISABLE_LOCAL=true`
    """
    global _OTEL_INITIALIZED
    if _OTEL_INITIALIZED:
        return

    cfg = _get_otel_config()
    if not cfg.enabled or cfg.mode == "none":
        _OTEL_INITIALIZED = True
        return

    available, otel = _lazy_import_otel()
    if not available:
        warnings.warn(
            "OpenTelemetry not installed; tracing disabled. Install with `pip install mcp-oci-opsi[observability]`.",
            UserWarning,
            stacklevel=2,
        )
        _OTEL_INITIALIZED = True
        return

    trace = otel["trace"]
    TracerProvider = otel["TracerProvider"]
    BatchSpanProcessor = otel["BatchSpanProcessor"]
    Resource = otel["Resource"]

    current_provider = trace.get_tracer_provider()
    if isinstance(current_provider, TracerProvider):
        _OTEL_INITIALIZED = True
        return

    resource = Resource.create(
        {
            "service.name": service_name,
            "service.namespace": os.getenv("OTEL_SERVICE_NAMESPACE", "mcp-oci"),
            "deployment.environment": os.getenv("DEPLOYMENT_ENVIRONMENT", os.getenv("ENVIRONMENT", "local")),
            "service.instance.id": f"{socket.gethostname()}-{os.getpid()}",
        }
    )

    exporter = _build_exporter(cfg)
    if exporter is None:
        _OTEL_INITIALIZED = True
        return

    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    _OTEL_INITIALIZED = True


def _build_exporter(cfg: OTelConfig):
    try:
        if cfg.mode in ("oci-apm", "otlp-http"):
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

            return OTLPSpanExporter(endpoint=cfg.endpoint, headers=cfg.headers)

        if cfg.mode == "otlp-grpc":
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

            endpoint = (cfg.endpoint or "").strip()
            endpoint = endpoint.removeprefix("http://").removeprefix("https://")
            return OTLPSpanExporter(endpoint=endpoint, insecure=True)
    except Exception as exc:
        warnings.warn(f"Failed to initialize OTLP exporter ({cfg.mode}): {exc}", UserWarning, stacklevel=2)
        return None
    return None


def instrument_requests() -> None:
    """Enable outgoing HTTP spans (OCI SDK uses requests). Non-fatal if deps are missing."""
    try:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor

        RequestsInstrumentor().instrument()
    except Exception:
        return


def instrument_fastapi(app: t.Any) -> None:
    """Enable FastAPI server spans for HTTP transports. Non-fatal if deps are missing."""
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    except Exception:
        return

    try:
        if hasattr(app, "app"):
            FastAPIInstrumentor.instrument_app(getattr(app, "app"))
            return
        if hasattr(app, "fastapi_app"):
            FastAPIInstrumentor.instrument_app(getattr(app, "fastapi_app"))
            return
    except Exception:
        return


def get_otel_status() -> dict[str, t.Any]:
    cfg = _get_otel_config()
    return {
        "enabled": bool(cfg.enabled and cfg.mode != "none"),
        "mode": cfg.mode,
        "oci_apm_configured": bool(os.getenv("OCI_APM_ENDPOINT") and os.getenv("OCI_APM_PRIVATE_DATA_KEY")),
        "otlp_endpoint_configured": bool(os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")),
        "local_fallback_disabled": os.getenv("OTEL_DISABLE_LOCAL", "false").lower() in ("1", "true", "yes", "on"),
    }

