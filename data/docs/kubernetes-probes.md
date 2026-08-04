# Kubernetes Health Probes

Kubernetes uses probes to decide whether a container is healthy and ready to
serve traffic. There are three probe types, and using them correctly is the
difference between a self-healing deployment and one that silently drops
requests.

## Liveness probes

A liveness probe answers "is this process stuck?". If it fails, the kubelet
restarts the container. Point liveness at a cheap endpoint that only fails when
the process is genuinely broken (for example, deadlocked). Avoid checking
downstream dependencies here, or a database blip will restart-loop your pods.

## Readiness probes

A readiness probe answers "can this pod accept traffic right now?". If it fails,
the pod is removed from the Service endpoints but is not restarted. This is the
right place to check that caches are warm, migrations have run, and required
dependencies are reachable.

## Startup probes

A startup probe protects slow-booting applications. Until it succeeds, liveness
and readiness checks are suspended, so a long JVM warm-up will not trip a
premature restart.

## Practical tips

- Set `initialDelaySeconds` and `failureThreshold` generously for slow starts,
  or prefer a dedicated startup probe.
- Keep probe endpoints lightweight; they run on every interval.
- Return distinct endpoints for liveness and readiness so they can fail
  independently.
