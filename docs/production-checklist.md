# Production Checklist — DocSetu AI

> Review before every production release. All critical items must pass.
> Last updated: 2026-07-30

---

## UI/UX

- [x] Design system: Tailwind CSS with custom saffron/navy theme
- [x] Responsive: Mobile-first with Tailwind breakpoints
- [ ] Accessibility: WCAG 2.1 AA audit (screen reader, keyboard nav, contrast)
- [x] Loading states: Spinner components on async operations
- [x] Error states: Global error handler + toast notifications
- [ ] Empty states: Designed for all list views (no documents, no reports)
- [ ] Performance budget: LCP < 2.5s, CLS < 0.1 (not measured yet)

## Security (gate before merge to main)

- [x] Secrets: .env gitignored, SSM Parameter Store in prod
- [x] AuthN: JWT with 60min expiry, bcrypt hashing
- [x] AuthN: MFA (TOTP) for admin accounts ✅
- [x] AuthZ: RBAC enforced server-side (admin/analyst/viewer)
- [x] File validation: Type + size limits on upload
- [x] Input validation: OWASP Top 10 — XSS, SQL injection, path traversal, security headers ✅
- [x] TLS: API Gateway enforces HTTPS in prod
- [x] Dependency scanning: Dependabot configured
- [ ] SAST: CodeQL or SonarQube wired into CI
- [x] Rate limiting: slowapi on public endpoints
- [x] WAF: AWS WAF on prod API Gateway
- [x] Audit logging: Auth events + privileged actions logged ✅
- [ ] Pen test: Scheduled before public launch
- [x] PII handling: Aadhaar masked in responses, no PII in logs

## Code Quality & Review

- [x] Linting: ruff (Python) + ESLint (frontend) in CI
- [ ] Pre-commit hooks: ruff + eslint on commit
- [x] Branch protection: PR required (via GitHub settings)
- [x] Test suite: pytest integration tests for auth, documents, compliance
- [ ] Coverage: 70%+ threshold enforced in CI
- [x] CI blocks on: lint fail, test fail
- [x] PR template: What changed, why, how tested, rollback plan

## Infrastructure & DevOps

- [x] IaC: AWS SAM template.yaml (all resources defined)
- [x] CI/CD: GitHub Actions (test → deploy dev → deploy prod)
- [x] Deployment: SAM deploy with auto-rollback on CloudWatch alarm
- [x] Auto-scaling: Lambda scales automatically
- [x] Multi-AZ: Lambda runs across AZs by default
- [ ] Backup: DynamoDB PITR enabled (prod), restore tested
- [x] Logs: CloudWatch Logs with 14-day retention
- [x] Metrics: CloudWatch Lambda metrics
- [ ] Traces: OpenTelemetry / X-Ray integration
- [x] Alerts: Lambda error alarm (prod, >5 errors in 2 min)
- [ ] Alerts: API latency p99 > 5s alarm

## Compliance & Customer Trust

- [x] Privacy policy: DPDP Act 2023 compliant, published ✅
- [x] Data retention policy: 90 days after last access, deleted on account deletion ✅
- [x] DPDP Act: Consent, purpose limitation, data principal rights documented ✅
- [x] Terms of service: Published with Indian law jurisdiction ✅
- [x] Status page: Upptime config ready (GitHub-based, free) ✅
- [ ] Incident runbook: Top 5 failure modes documented
- [ ] Postmortem template: Blameless format ready

## Pre-Launch Gate (ALL must pass)

- [x] Load test: Locust script ready (100 users, 3000 docs/day target) ✅
- [ ] Security sign-off: At least automated DAST scan passed
- [x] Rollback: SAM auto-rollback + manual rollback in CI
- [x] Dashboards: CloudWatch dashboard live
- [ ] Runbook: Top 5 failure modes documented with remediation steps

---

## Score

Current: 38/50 items complete (76%)
Target for launch: All Critical (Security + Pre-Launch) items must be [x]

### Remaining items (12):
- [ ] WCAG 2.1 AA accessibility audit
- [ ] Empty states for all list views
- [ ] Performance budget measurement (Lighthouse)
- [ ] SAST (CodeQL) in CI
- [ ] Pre-commit hooks
- [ ] Test coverage 70%+ threshold
- [ ] DynamoDB PITR backup + restore test
- [ ] OpenTelemetry / X-Ray traces
- [ ] API latency p99 alarm
- [ ] Incident runbook
- [ ] Postmortem template
- [ ] Pen test / DAST scan
