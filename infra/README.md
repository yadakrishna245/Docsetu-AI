# DocSetu AI — Infrastructure Documentation

> Serverless deployment guide for the DocSetu AI document intelligence platform.

---

## Architecture Diagram

```
                                    ┌─────────────────────────────────────────────────────────┐
                                    │                    AWS Cloud                             │
                                    │                                                         │
                                    │  ┌───────────────┐    ┌──────────────┐                  │
                                    │  │  CloudWatch   │    │   IAM Roles  │                  │
                                    │  │  Logs/Metrics │    │  & Policies  │                  │
                                    │  └───────┬───────┘    └──────┬───────┘                  │
                                    │          │                   │                          │
┌──────────┐   HTTPS    ┌──────────┴──────┐   │    ┌──────────────┴───────┐                  │
│          │───────────▶│  API Gateway    │   │    │                      │                  │
│  Client  │            │  (REST API)     │   ▼    ▼                      │                  │
│  (Web/   │◀───────────│  + WAF         │───────────┐                   │                  │
│  Mobile) │   JSON     └────────┬────────┘          │                   │                  │
└──────────┘                     │                   │                   │                  │
                                 ▼                   │                   │                  │
                        ┌────────────────┐           │                   │                  │
                        │   AWS Lambda   │◀──────────┘                   │                  │
                        │  (Python 3.11) │                               │                  │
                        │                │───────┐                       │                  │
                        └───┬────────┬───┘       │                       │                  │
                            │        │           │                       │                  │
                            ▼        ▼           ▼                       │                  │
                   ┌────────────┐ ┌─────┐  ┌─────────┐                  │                  │
                   │  DynamoDB  │ │ S3  │  │  SSM     │                  │                  │
                   │  (NoSQL)   │ │Bucket│  │Parameter│                  │                  │
                   │            │ │     │  │  Store   │                  │                  │
                   └────────────┘ └─────┘  └─────────┘                  │                  │
                                    │                                    │                  │
                                    └────────────────────────────────────┘                  │
                                                                                           │
                                    └─────────────────────────────────────────────────────────┘
```

### Component Summary

| Component | Purpose |
|-----------|---------|
| **API Gateway** | HTTPS entry point, request validation, throttling |
| **AWS Lambda** | Core business logic — document parsing, AI inference |
| **DynamoDB** | Document metadata, user sessions, processing state |
| **S3** | Raw document storage (PDFs, images, processed outputs) |
| **SSM Parameter Store** | Secrets & configuration (API keys, feature flags) |
| **CloudWatch** | Logs, metrics, dashboards, alarms |
| **IAM** | Least-privilege access control for all services |

---

## Prerequisites

Before deploying, ensure you have the following installed and configured:

| Requirement | Version | Verify Command |
|-------------|---------|----------------|
| AWS Account | Admin access (or scoped deploy role) | `aws sts get-caller-identity` |
| AWS CLI | v2.x | `aws --version` |
| SAM CLI | ≥ 1.100.0 | `sam --version` |
| Python | 3.11.x | `python --version` |
| PowerShell | 5.1+ | `$PSVersionTable.PSVersion` |
| Git | 2.x+ | `git --version` |
| Docker | (optional, for local testing) | `docker --version` |

### AWS CLI Configuration

```powershell
# Configure default profile
aws configure
# AWS Access Key ID: <your-key>
# AWS Secret Access Key: <your-secret>
# Default region: ap-south-1
# Default output format: json

# Verify
aws sts get-caller-identity
```

---

## Quick Start

Deploy DocSetu AI in 3 commands:

```powershell
# 1. Clone the repository
git clone https://github.com/your-org/Docsethu-AI.git

# 2. Navigate to project root
cd Docsethu-AI

# 3. Deploy to dev environment
.\deploy.ps1 -Stage dev
```

The `deploy.ps1` script handles:
- ✅ Dependency installation (`pip install`)
- ✅ SAM build & package
- ✅ CloudFormation stack deployment
- ✅ SSM parameter seeding (first run)
- ✅ Output of API endpoint URL

### Deploy Options

```powershell
# Deploy to production
.\deploy.ps1 -Stage prod

# Deploy with custom region
.\deploy.ps1 -Stage dev -Region us-east-1

# Deploy with verbose logging
.\deploy.ps1 -Stage dev -Verbose

# Destroy stack
.\deploy.ps1 -Stage dev -Destroy
```

---

## Cost Estimation

### AWS Free Tier Coverage (first 12 months)

| Service | Free Tier Limit |
|---------|----------------|
| API Gateway | 1M REST API calls/month |
| Lambda | 1M requests + 400,000 GB-seconds/month |
| DynamoDB | 25 GB storage, 25 RCU, 25 WCU |
| S3 | 5 GB storage, 20K GET, 2K PUT requests |
| CloudWatch | 10 custom metrics, 10 alarms, 5 GB logs |

### Estimated Monthly Costs (beyond free tier)

#### Light Usage — 10K documents/month: **~$5–15**

| Service | Usage | Cost |
|---------|-------|------|
| API Gateway | ~50K requests | $0.18 |
| Lambda | ~50K invocations, 128MB, 3s avg | $0.30 |
| DynamoDB | 5 GB, on-demand | $1.25 |
| S3 | 10 GB stored, 30K requests | $0.50 |
| CloudWatch | Logs + metrics | $2.00 |
| **Total** | | **~$4–5** |

#### Medium Usage — 100K documents/month: **~$30–50**

| Service | Usage | Cost |
|---------|-------|------|
| API Gateway | ~500K requests | $1.75 |
| Lambda | ~500K invocations, 256MB, 5s avg | $5.20 |
| DynamoDB | 25 GB, on-demand | $6.25 |
| S3 | 100 GB stored, 300K requests | $3.50 |
| CloudWatch | Logs + metrics + dashboards | $8.00 |
| Data Transfer | ~50 GB outbound | $4.50 |
| **Total** | | **~$30–50** |

> 💡 **Tip:** Use the [AWS Pricing Calculator](https://calculator.aws/) for precise estimates based on your region.

---

## Environment Variables

### Lambda Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `STAGE` | Deployment stage | `dev`, `staging`, `prod` |
| `DOCUMENTS_TABLE` | DynamoDB table name | `docsetu-docs-dev` |
| `USERS_TABLE` | DynamoDB users table | `docsetu-users-dev` |
| `S3_BUCKET` | Document storage bucket | `docsetu-documents-dev` |
| `SSM_PREFIX` | SSM parameter path prefix | `/docsetu/dev` |
| `LOG_LEVEL` | Logging verbosity | `INFO`, `DEBUG` |
| `MAX_DOCUMENT_SIZE_MB` | Upload size limit | `25` |
| `AI_MODEL_ENDPOINT` | ML inference endpoint | `arn:aws:sagemaker:...` |
| `CORS_ORIGINS` | Allowed CORS origins | `https://docsetu.ai` |
| `RATE_LIMIT_PER_USER` | Requests per minute per user | `60` |

### Managing Secrets via SSM Parameter Store

```powershell
# Set a secret (SecureString — encrypted with KMS)
aws ssm put-parameter `
  --name "/docsetu/dev/OPENAI_API_KEY" `
  --value "sk-..." `
  --type "SecureString" `
  --overwrite

# List all DocSetu parameters
aws ssm get-parameters-by-path `
  --path "/docsetu/dev" `
  --recursive `
  --with-decryption

# Update an existing parameter
aws ssm put-parameter `
  --name "/docsetu/dev/LOG_LEVEL" `
  --value "DEBUG" `
  --type "String" `
  --overwrite
```

### SSM Parameters Used

| Parameter Path | Type | Description |
|----------------|------|-------------|
| `/docsetu/{stage}/OPENAI_API_KEY` | SecureString | OpenAI API key for AI features |
| `/docsetu/{stage}/JWT_SECRET` | SecureString | JWT signing secret |
| `/docsetu/{stage}/WEBHOOK_SECRET` | SecureString | Webhook validation secret |
| `/docsetu/{stage}/LOG_LEVEL` | String | Runtime log level |
| `/docsetu/{stage}/FEATURE_FLAGS` | String | JSON feature flag config |

---

## Monitoring

### CloudWatch Dashboard Setup

Deploy the monitoring dashboard:

```powershell
aws cloudformation deploy `
  --template-file infra/monitoring-dashboard.yaml `
  --stack-name docsetu-monitoring-dev `
  --parameter-overrides Stage=dev
```

Or create manually via CLI:

```powershell
aws cloudwatch put-dashboard `
  --dashboard-name "DocSetu-Dev" `
  --dashboard-body (Get-Content -Raw infra/dashboard.json)
```

### Key Metrics to Watch

| Metric | Namespace | Threshold | Action |
|--------|-----------|-----------|--------|
| Lambda Duration | AWS/Lambda | > 10s (p99) | Optimize code or increase memory |
| Lambda Errors | AWS/Lambda | > 5/min | Check logs immediately |
| Lambda Throttles | AWS/Lambda | > 0 | Increase concurrency limit |
| API Gateway 5xx | AWS/ApiGateway | > 1% of requests | Investigate Lambda errors |
| API Gateway Latency | AWS/ApiGateway | > 5s (p95) | Check cold starts |
| DynamoDB ThrottledRequests | AWS/DynamoDB | > 0 | Switch to on-demand or increase capacity |
| S3 4xx Errors | AWS/S3 | > 10/min | Check permissions or client code |

### Alarm Configuration

```powershell
# Lambda error rate alarm
aws cloudwatch put-metric-alarm `
  --alarm-name "DocSetu-Lambda-Errors-Dev" `
  --metric-name "Errors" `
  --namespace "AWS/Lambda" `
  --dimensions "Name=FunctionName,Value=docsetu-api-dev" `
  --statistic "Sum" `
  --period 300 `
  --threshold 5 `
  --comparison-operator "GreaterThanThreshold" `
  --evaluation-periods 2 `
  --alarm-actions "arn:aws:sns:ap-south-1:123456789:docsetu-alerts"

# API Gateway 5xx alarm
aws cloudwatch put-metric-alarm `
  --alarm-name "DocSetu-API-5xx-Dev" `
  --metric-name "5XXError" `
  --namespace "AWS/ApiGateway" `
  --dimensions "Name=ApiName,Value=docsetu-api-dev" `
  --statistic "Sum" `
  --period 60 `
  --threshold 10 `
  --comparison-operator "GreaterThanThreshold" `
  --evaluation-periods 1 `
  --alarm-actions "arn:aws:sns:ap-south-1:123456789:docsetu-alerts"
```

---

## Scaling

### Lambda Concurrency

```powershell
# Set reserved concurrency (guarantees capacity)
aws lambda put-function-concurrency `
  --function-name "docsetu-api-dev" `
  --reserved-concurrent-executions 100

# Set provisioned concurrency (eliminates cold starts)
aws lambda put-provisioned-concurrency-config `
  --function-name "docsetu-api-dev" `
  --qualifier "prod" `
  --provisioned-concurrent-executions 10
```

| Stage | Reserved Concurrency | Provisioned Concurrency |
|-------|---------------------|------------------------|
| dev | 10 | 0 (not needed) |
| staging | 50 | 0 |
| prod | 200 | 10 |

### DynamoDB Auto-Scaling

For provisioned capacity mode (cost-optimized for predictable workloads):

```powershell
# Register scalable target
aws application-autoscaling register-scalable-target `
  --service-namespace "dynamodb" `
  --resource-id "table/docsetu-docs-prod" `
  --scalable-dimension "dynamodb:table:ReadCapacityUnits" `
  --min-capacity 5 `
  --max-capacity 100

# Create scaling policy
aws application-autoscaling put-scaling-policy `
  --service-namespace "dynamodb" `
  --resource-id "table/docsetu-docs-prod" `
  --scalable-dimension "dynamodb:table:ReadCapacityUnits" `
  --policy-name "DocSetuReadAutoScaling" `
  --policy-type "TargetTrackingScaling" `
  --target-tracking-scaling-policy-configuration '{
    \"TargetValue\": 70.0,
    \"PredefinedMetricSpecification\": {
      \"PredefinedMetricType\": \"DynamoDBReadCapacityUtilization\"
    }
  }'
```

> 💡 **Recommendation:** Use **on-demand** mode for dev/staging (no capacity planning needed). Use **provisioned + auto-scaling** for prod if usage is predictable.

### API Gateway Throttling

```powershell
# Set stage-level throttling
aws apigateway update-stage `
  --rest-api-id "abc123xyz" `
  --stage-name "prod" `
  --patch-operations '[
    {"op": "replace", "path": "/*/*/throttling/rateLimit", "value": "1000"},
    {"op": "replace", "path": "/*/*/throttling/burstLimit", "value": "2000"}
  ]'
```

| Stage | Rate Limit (req/sec) | Burst Limit |
|-------|---------------------|-------------|
| dev | 100 | 200 |
| staging | 500 | 1000 |
| prod | 1000 | 2000 |

---

## Troubleshooting

### Common Deployment Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `CREATE_FAILED: Resource already exists` | Stack name collision | Delete existing stack or use different stage name |
| `Unable to upload artifact` | S3 bucket permissions | Verify `aws sts get-caller-identity` has S3 access |
| `Runtime.ImportModuleError` | Missing Python dependency | Run `pip install -r requirements.txt -t ./package/` |
| `ROLLBACK_COMPLETE` | CloudFormation failed | Check Events tab in CloudFormation console |
| `AccessDeniedException` | Insufficient IAM permissions | Attach `AdministratorAccess` or scoped deploy policy |
| `Template format error` | Invalid SAM template | Run `sam validate` to check syntax |

### Checking Lambda Logs

```powershell
# Tail logs in real time
sam logs -n DocSetuApiFunction --stack-name docsetu-dev --tail

# Filter for errors
aws logs filter-log-events `
  --log-group-name "/aws/lambda/docsetu-api-dev" `
  --filter-pattern "ERROR" `
  --start-time (Get-Date).AddHours(-1).ToUnixTimeMilliseconds()

# Get recent log streams
aws logs describe-log-streams `
  --log-group-name "/aws/lambda/docsetu-api-dev" `
  --order-by "LastEventTime" `
  --descending `
  --limit 5
```

### Local Testing with SAM

```powershell
# Build the application
sam build

# Start local API (requires Docker)
sam local start-api --env-vars env.json

# Invoke a single function
sam local invoke DocSetuApiFunction `
  --event events/test-upload.json `
  --env-vars env.json

# Generate sample events
sam local generate-event apigateway aws-proxy `
  --method POST `
  --path "/api/documents" `
  --body '{"filename": "test.pdf"}' > events/test-upload.json
```

Create an `env.json` for local testing:

```json
{
  "DocSetuApiFunction": {
    "STAGE": "local",
    "DOCUMENTS_TABLE": "docsetu-docs-dev",
    "USERS_TABLE": "docsetu-users-dev",
    "S3_BUCKET": "docsetu-documents-dev",
    "LOG_LEVEL": "DEBUG"
  }
}
```

### Health Check

```powershell
# Quick health check after deployment
$apiUrl = (aws cloudformation describe-stacks `
  --stack-name docsetu-dev `
  --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" `
  --output text)

Invoke-RestMethod -Uri "$apiUrl/health" -Method GET
```

---

## CI/CD

### Option 1: GitHub Actions (Recommended)

See [`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml) for the full workflow.

**Key features:**
- OIDC authentication (no long-lived AWS keys)
- Deploys to `dev` on PR, `prod` on main merge
- Runs tests before deploy
- Includes rollback on failure

**Setup steps:**

1. Create an OIDC identity provider in AWS IAM:
   ```powershell
   aws iam create-open-id-connect-provider `
     --url "https://token.actions.githubusercontent.com" `
     --client-id-list "sts.amazonaws.com" `
     --thumbprint-list "6938fd4d98bab03faadb97b34396831e3780aea1"
   ```

2. Create a deploy role with trust policy for your repo:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Principal": {
           "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
         },
         "Action": "sts:AssumeRoleWithWebIdentity",
         "Condition": {
           "StringEquals": {
             "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
           },
           "StringLike": {
             "token.actions.githubusercontent.com:sub": "repo:your-org/Docsethu-AI:*"
           }
         }
       }
     ]
   }
   ```

3. Add the role ARN as a GitHub repository secret: `AWS_DEPLOY_ROLE_ARN`

### Option 2: AWS CodePipeline

For teams preferring AWS-native CI/CD:

```powershell
# Deploy CodePipeline stack
aws cloudformation deploy `
  --template-file infra/pipeline.yaml `
  --stack-name docsetu-pipeline `
  --capabilities CAPABILITY_IAM `
  --parameter-overrides `
    GitHubOwner=your-org `
    GitHubRepo=Docsethu-AI `
    GitHubBranch=main `
    GitHubOAuthToken=ghp_xxxxx
```

Pipeline stages:
1. **Source** — GitHub webhook trigger
2. **Build** — CodeBuild runs `sam build` + tests
3. **Deploy-Dev** — Auto-deploy to dev
4. **Approval** — Manual approval gate
5. **Deploy-Prod** — Deploy to production

---

## Security Best Practices

- ✅ All secrets in SSM Parameter Store (SecureString)
- ✅ Least-privilege IAM roles per Lambda function
- ✅ API Gateway WAF integration
- ✅ HTTPS only (TLS 1.2+)
- ✅ VPC endpoints for DynamoDB and S3 (no internet traversal)
- ✅ CloudTrail enabled for audit logging
- ✅ No long-lived access keys in CI/CD (OIDC)

---

## Useful Commands Reference

```powershell
# Check stack status
aws cloudformation describe-stacks --stack-name docsetu-dev

# List all stack resources
aws cloudformation list-stack-resources --stack-name docsetu-dev

# Get API endpoint
aws cloudformation describe-stacks --stack-name docsetu-dev `
  --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text

# Delete stack (WARNING: destroys all resources)
aws cloudformation delete-stack --stack-name docsetu-dev

# View SAM template
sam validate --template template.yaml
```

---

## Support

- 📖 [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- 🐛 File issues on the GitHub repository
- 💬 Team Slack: `#docsetu-infra`
