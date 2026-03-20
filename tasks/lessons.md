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

