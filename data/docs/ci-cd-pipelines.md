# CI/CD Pipelines

A CI/CD pipeline automates the path from a code commit to a running release.
Continuous integration (CI) builds and tests every change; continuous delivery
or deployment (CD) promotes passing builds toward production.

## Continuous integration

On each push or pull request, the pipeline checks out the code, installs
dependencies, and runs linters, type checks, and the test suite. Fast, reliable
CI gives developers quick feedback and keeps the main branch releasable. Cache
dependencies and parallelize test jobs to keep the loop short.

## Continuous delivery vs deployment

- **Continuous delivery** produces a deployable artifact for every green build,
  but a human approves the final promotion to production.
- **Continuous deployment** removes that gate: every change that passes the
  pipeline ships automatically.

## Pipeline stages

A typical pipeline flows through build, test, package (for example, a container
image), and deploy stages. Later stages should only run if earlier ones pass,
and secrets used for deployment should come from a secret manager rather than
being hard-coded in pipeline configuration.

## Good practice

- Keep pipelines fast; slow pipelines get bypassed.
- Make builds reproducible and artifacts immutable.
- Fail loudly and surface logs so failures are easy to diagnose.
- Treat pipeline definitions as versioned code, reviewed like anything else.
