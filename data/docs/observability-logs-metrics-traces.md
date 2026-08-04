# Observability: Logs, Metrics, and Traces

Observability is the ability to understand a system's internal state from the
signals it emits. The three classic pillars are logs, metrics, and traces, and
each answers a different question.

## Logs

Logs are timestamped records of discrete events. They are rich in detail and
ideal for debugging a specific incident, but high volume makes them expensive to
store and search. Prefer structured (JSON) logs with consistent fields so they
can be queried, and attach a correlation ID to tie related events together.

## Metrics

Metrics are numeric measurements aggregated over time -- request rate, error
rate, latency percentiles, CPU usage. They are cheap to store and perfect for
dashboards and alerting because they summarize behavior rather than record every
event. Metrics tell you *that* something is wrong.

## Traces

Distributed traces follow a single request as it hops across services, recording
the timing of each span. They tell you *where* time is spent and which
downstream call is the bottleneck, which is invaluable in a microservices
architecture.

## Putting it together

Use metrics to detect a problem and alert on it, traces to localize which
service is responsible, and logs to see the precise detail of what happened.
OpenTelemetry provides a vendor-neutral way to instrument all three from one set
of libraries.
