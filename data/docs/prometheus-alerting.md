# Prometheus Alerting

Prometheus evaluates alerting rules against collected time-series metrics and
forwards firing alerts to Alertmanager, which handles grouping, silencing, and
routing to receivers like email, Slack, or PagerDuty.

## Alerting rules

Rules live in rule files and are written in PromQL. Each rule has an `expr`, a
`for` duration that the condition must hold before firing, and labels and
annotations for context:

```yaml
- alert: HighRequestLatency
  expr: job:request_latency_seconds:mean5m{job="api"} > 0.5
  for: 10m
  labels:
    severity: page
  annotations:
    summary: "High request latency on {{ $labels.instance }}"
```

The `for` clause suppresses flapping by requiring the condition to persist.

## Alertmanager

Alertmanager deduplicates and groups related alerts so a single incident does
not page you a hundred times. Routing trees send different severities to
different receivers, and inhibition rules mute downstream alerts when a parent
alert is already firing.

## Good practice

- Alert on symptoms users feel (latency, error rate), not just causes.
- Every alert should be actionable and link to a runbook.
- Use severity labels to separate "wake someone up" from "look at it tomorrow".
