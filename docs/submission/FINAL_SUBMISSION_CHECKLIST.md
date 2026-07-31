# Final Submission Checklist

## Repository

- [ ] Public repository URL added to README.
- [ ] Default branch selected.
- [ ] No secrets tracked.
- [ ] No confidential assignment PDF tracked.
- [ ] README complete.

## Backend

- [ ] Railway backend URL added.
- [ ] `/api/v1/health` returns healthy.
- [ ] Alembic migration completed.
- [ ] Persistent SQLite volume mounted.
- [ ] `DATABASE_URL` points to volume path.
- [ ] `CORS_ALLOWED_ORIGINS` includes frontend URL.
- [ ] NVIDIA key configured or fallback noted.

## Frontend

- [ ] Vercel frontend URL added.
- [ ] `VITE_API_BASE_URL` points to backend.
- [ ] Deep links work for Reports, Reconciliation, Analytics, and Narrative.
- [ ] Mobile layout reviewed.

## Product

- [ ] Import works.
- [ ] Reconciliation works.
- [ ] Analytics works.
- [ ] AI Summary works.
- [ ] Traced Figures work.
- [ ] Fallback works without NVIDIA key.
- [ ] Empty day works.
- [ ] Refund-only day works.
- [ ] Partial import and issue drawer work.

## Submission

- [ ] Repo link submitted.
- [ ] Live frontend link submitted.
- [ ] Backend URL available if requested.
- [ ] Demo video link submitted.
- [ ] Screenshots prepared from synthetic data.
- [ ] Notes mention deterministic fallback when NVIDIA is not configured.
