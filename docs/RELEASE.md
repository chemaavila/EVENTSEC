# Release Guide

## Version alignment checklist

Before releasing, ensure the following stay aligned:

- Docker base images in `backend/Dockerfile.backend`, `email_protection/Dockerfile`,
  `protoxol_triage_package/Dockerfile`, and `frontend/Dockerfile.frontend`.
- GitHub Actions runtime versions in `.github/workflows/ci.yml`.
- Local developer defaults in `.python-version` and `.nvmrc`.
- Compose and Kubernetes manifests in `docker-compose.yml` and `deploy/k8s/*`.

## Suggested release steps

1. Update dependencies (Python `requirements.txt`, frontend `package.json`/lockfile) in a
   single PR.
2. Run the verification playbook (see `docs/TROUBLESHOOTING.md` for common failures).
3. Confirm tenant data lake policies remain disabled by default after migrations.
4. Tag a release and publish images with a concrete version tag (avoid `latest`).

## Rollback

If a release introduces regressions:

1. Re-deploy the previous tag for backend/frontend images.
2. Re-run `alembic downgrade -1` if a database migration must be reverted (ensure the
   downgrade path is valid).
