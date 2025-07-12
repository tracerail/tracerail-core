# tracerail/tracing.py
import os
from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

def setup_tracing(service_name: str):
    """
    Configures and enables OpenTelemetry tracing for the worker.

    This function sets up a tracer that exports spans to a Jaeger collector
    via the OTLP gRPC protocol, which is the standard for OpenTelemetry.
    """
    # A Resource is a collection of attributes that describe the application.
    # The 'service.name' is a standard attribute that Jaeger uses to identify our service.
    resource = Resource(attributes={
        SERVICE_NAME: service_name
    })

    # The TracerProvider is the main entry point for the OpenTelemetry SDK.
    provider = TracerProvider(resource=resource)

    # The OTLP Exporter is responsible for sending the trace data (spans).
    # We configure it to send to our Jaeger container. The endpoint is read from
    # an environment variable for flexibility, defaulting to the Docker service name.
    jaeger_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "jaeger:4317")
    otlp_exporter = OTLPSpanExporter(
        endpoint=jaeger_endpoint,
        insecure=True  # Use an insecure connection for local development.
    )

    # The BatchSpanProcessor is a more performant way to send traces. It
    # collects spans into batches before sending them to the exporter.
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Set our configured provider as the global default. Any part of the
    # application that asks for a tracer will now get one from this provider.
    trace.set_tracer_provider(provider)

    print(f"✅ OpenTelemetry tracing configured for '{service_name}', exporting to {jaeger_endpoint}")
