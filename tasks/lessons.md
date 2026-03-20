# Lessons Learned

## Phase 1

- Treat repository truthfulness as a testable contract. Public documentation
  must match the actual runtime boundary, source ownership, and legal status of
  the repo.
- Protect internal-only services at the application transport boundary, not only
  with network segmentation. The MCP bridge now enforces an explicit bearer
  token and fails closed when the token is missing.
- Production identity policy must be explicit and mandatory. Wildcard Entra
  access defaults are incompatible with a hardened zero-trust posture.
- Repository-controlled production artifacts must use immutable image references
  or explicit digest placeholders. Floating `latest` tags and `imagePullPolicy:
  Always` were removed from production-owned paths.
- CI/security baselines should be codified with contract tests so workflow drift
  is caught locally before it reaches the remote pipeline.

## Phase 2

- Reproducibility needs to be enforced at the install path, not just documented
  in package metadata. Lockfiles only matter if Docker and CI consume them
  directly.
- Integration coverage should test the public entrypoints and CI wiring, not
  only helper functions. Matrix contracts now protect that boundary.
- Observability baselines should provide a collector path even before a full
  LGTM backend is deployed. Grafana Alloy with OTLP ingress and debug exporters
  is a valid first operational step.
- Runtime hardening benefits from layering: process limits in Compose plus
  namespace and network policy controls in Kubernetes.
- Release engineering should publish immutable artifacts and metadata together.
  Container tags alone are insufficient without provenance, SBOM, and a release
  manifest artifact.

