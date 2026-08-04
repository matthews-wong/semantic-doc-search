# IAM Least Privilege

The principle of least privilege says every identity -- user, service account,
or workload -- should have only the permissions it needs to do its job, and no
more. Tight IAM policies shrink the blast radius when a credential leaks or a
service is compromised.

## Building least-privilege policies

- Start from zero and add permissions as concrete needs appear, rather than
  granting broad wildcards and trimming later.
- Prefer specific actions and resource ARNs over `*`.
- Use conditions (source IP, MFA present, tag match) to constrain when a
  permission applies.
- Separate roles by function so a read-only reporting job cannot mutate data.

## Roles over long-lived keys

Assign permissions to roles that workloads assume for short-lived credentials
instead of embedding static access keys. On AWS this means instance profiles or
IRSA for EKS; on GCP, workload identity; on Azure, managed identities. Rotate
any remaining static secrets automatically.

## Keeping policies honest

Permissions drift as systems evolve. Periodically review access with tooling
that flags unused permissions (for example, AWS IAM Access Analyzer) and prune
what is no longer exercised. Audit logs tell you what was actually used, which
is the best guide to what can be safely removed.
