# Production Checklist — DocSetu AI

> Review before every production release. All critical items must pass.

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
- [ ] AuthN: MFA for admin accounts
- [x] AuthZ: RBAC enforced server-side (admin/analyst/viewer)
- [x] File validation: Type + size limits on upload
- [ ] Input validation: Full OWASP Top 10 audit
- [x] TLS: API Gateway enforces HTTPS in prod
- [x] Dependency scanning: Dependabot configured
- [ ] SAST: CodeQL or SonarQube wired into CI
- [x] Rate limiting: slowapi on public endpoints
- [x] WAF: AWS WAF on prod API Gateway
- [ ] Audit logging: Auth events + privileged actions logged
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

- [ ] Privacy policy: Published on website
- [ ] Data retention policy: Defined (how long docs stored)
- [ ] DPDP Act: Consent mechanism, data deletion on request
- [ ] Terms of service: Published
- [ ] Status page: Public uptime monitor
- [ ] Incident runbook: Top 5 failure modes documented
- [ ] Postmortem template: Blameless format ready

## Pre-Launch Gate (ALL must pass)

- [ ] Load test: 3x peak (3000 docs/day simulated)
- [ ] Security sign-off: At least automated DAST scan passed
- [x] Rollback: SAM auto-rollback + manual rollback in CI
- [x] Dashboards: CloudWatch dashboard live
- [ ] Runbook: Top 5 failure modes documented with remediation steps

---

## Score

Current: 27/50 items complete (54%)
Target for launch: All Critical (Security + Pre-Launch) items must be [x]
