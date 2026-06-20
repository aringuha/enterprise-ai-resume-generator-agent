# Enterprise Readiness

This project now includes production-style foundations that can run locally and be promoted into a real enterprise environment.

## Implemented Locally

- FastAPI backend with layered route, auth, orchestrator, agent workflow, and structured response.
- Streamlit UI with login gate, resume/job upload options, manual fields, and TXT/JSON downloads.
- Signed JWT bearer token validation, static development bearer token support, and legacy `X-API-Key` support.
- Request ID middleware with `X-Request-ID` propagation.
- Audit-style request completion logs.
- Security headers.
- CORS allowlist.
- In-memory rate limiting for local/demo use.
- `/health`, `/ready`, `/metrics`, and `/metrics/json` operational endpoints.
- PDF, DOCX, TXT, and Markdown text extraction endpoint.
- Resume export endpoint for downloadable plain text.
- Docker Compose healthchecks.
- Non-root Docker runtime user.
- Kubernetes deployment/service/readiness/liveness scaffolding.
- GitHub Actions test workflow.
- Unit/API tests for security, readiness, metrics, upload extraction, export, workflow behavior, and API generation.

## Production Integrations Still Required

These cannot be completed without organization-specific accounts, DNS, secrets, and infrastructure:

- Google Workspace, Microsoft Entra ID, Okta, or another OIDC provider.
- OAuth client ID, client secret, issuer URL, redirect URL, and group/role mappings.
- TLS certificate and production domain.
- Real secret manager such as AWS Secrets Manager, Azure Key Vault, Google Secret Manager, or HashiCorp Vault.
- Container registry and deployment target.
- Production Ollama host or managed model gateway.
- Centralized log, trace, and metrics backend such as OpenTelemetry Collector, Prometheus, Grafana, Datadog, or CloudWatch.
- Malware scanning service for uploaded files.
- Persistent encrypted database or object storage if generated resumes should be saved.

## Recommended Production Auth Path

For enterprise login, use OIDC instead of static API keys:

1. Register the app with Google Workspace, Microsoft Entra ID, or Okta.
2. Configure callback URL for the deployed UI.
3. Store OAuth client secret in a secret manager.
4. Validate ID token issuer, audience, expiry, and signature.
5. Map groups/claims to app roles.
6. Keep API authorization as JWT bearer validation.

## Deployment Notes

The Kubernetes manifest in `deploy/kubernetes/enterprise-ai-resume-generator.yaml` is a starting point. Before production:

- Replace all secret placeholders.
- Push the Docker image to a registry.
- Configure ingress with TLS.
- Set `CORS_ORIGINS` to the deployed UI origin only.
- Point `OLLAMA_BASE_URL` to a reachable model service.
- Replace in-memory rate limiting with Redis/API gateway rate limiting for multi-replica deployments.
