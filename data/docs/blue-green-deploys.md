# Blue-Green Deployments

A blue-green deployment runs two identical production environments, only one of
which serves live traffic at a time. The active environment is "blue"; you
deploy the new release to the idle "green" environment, verify it, then switch
traffic over. Rollback is instant -- you just point traffic back at blue.

## The switch

Traffic cutover happens at a load balancer, DNS record, or service mesh route.
Because green is already warm and tested before the switch, users experience no
deploy-time downtime, and a bad release can be reverted in seconds.

## Trade-offs

- **Cost**: you temporarily run double the infrastructure.
- **Stateful services**: databases and queues are shared or migrated carefully,
  since you cannot duplicate live data trivially. Backwards-compatible schema
  changes make cutover and rollback safe.
- **Long-lived connections**: drain existing sessions gracefully before
  decommissioning the old environment.

## Related strategies

Canary releases shift a small percentage of traffic to the new version and ramp
up gradually, giving finer-grained risk control at the cost of more complex
routing. Rolling updates replace instances in batches without a second full
environment. Blue-green shines when you want a clean, instant, all-or-nothing
switch with a trivial rollback.
