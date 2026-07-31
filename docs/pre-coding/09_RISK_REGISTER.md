# Risk Register

| Risk | Probability | Impact | Mitigation | Owner/check |
|---|---|---|---|---|
| NVIDIA endpoint unavailable/rate-limited | Medium | Medium | 20 s timeout, one repair/retry where applicable, deterministic fallback | Narrative tests/live smoke |
| Model violates structured output | Medium | High | Pydantic schema, placeholder validator, one repair, fallback | Agentic test suite |
| Model invents numbers | Medium | Critical | literal digits forbidden; backend inserts all values | Grounding tests |
| Narrative becomes stale after re-import | Low | High | report hash binding and atomic invalidation | Integration test |
| Rejected-row count incorrect | Confirmed | Medium | unique row-index count fix | Regression test |
| SQLite data lost on deploy | Medium without volume | High | Railway volume `/app/data`; persistence check | Deployment checklist |
| SQLite cannot scale horizontally | Certain | Low for assignment | one replica; document assignment constraint | README |
| Public endpoint burns NVIDIA quota | Medium | Medium | cache narrative, per-IP rate limit, disabled repeated clicks | Rate-limit test |
| API key leaks to frontend/repo/logs | Low | Critical | backend env only, secret scan, no prompt/raw logging | Final repo audit |
| Confidential assignment files published | Low | High | `.gitignore`, synthetic fixtures, clean zip/repo audit | Submission checklist |
| UI diverges from provided mockups | Medium | High | screen-by-screen acceptance review, minimal extra UI | Manual visual check |
| Frontend recomputes metrics differently | Low | High | server values only; no calculation utilities except formatting | Code review/tests |
| Empty-day date cannot be inferred | Addressed | High | route clinic/date authoritative | Empty-day API test |
| Refunds pollute sales rankings | Low | High | deterministic exclusion + tests | Refund-only tests |
| Medicine typo silently merged | Low | Medium | normalization only; warning without merge | Existing test |
| UTC hour misunderstood as local time | Medium | Medium | `UTC` labels in API/UI/narrative | UI test/manual review |
| Large malformed body exhausts API | Medium | Medium | 5 MB body and 10k row limits | 413 tests |
| Raw clinic rows retained unnecessarily | Medium | Medium | raw-row storage off by default | Persistence test |
| New dependency versions break build | Medium | Medium | pin compatible versions, lockfiles, CI | Clean-install job |
| Free hosting cold start hurts demo | Medium | Low | open link before interview; health endpoint; fallback local | Demo checklist |

## Risk acceptance

Authentication, multi-tenancy, regulatory compliance, and horizontal scaling are deliberately not implemented because the evaluation uses synthetic data and constrains storage to SQLite/in-memory. These limitations must be stated clearly, not hidden.
