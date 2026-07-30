#Requires -Version 5.1
<#
.SYNOPSIS
    DocSetu AI - Single-Click Serverless Deployment Script
.DESCRIPTION
    Deploys the DocSetu AI serverless application using AWS SAM.
    Handles S3 bucket creation, secrets management, build, and deployment.
.PARAMETER Stage
    Deployment stage (dev or prod). Default: dev
.PARAMETER Region
    AWS region for deployment. Default: ap-south-1
.PARAMETER StackName
    CloudFormation stack name. Default: docsetu-ai
.PARAMETER OpenAIKey
    Optional OpenAI API key for AI features
.PARAMETER SkipBuild
    Skip SAM build step (useful for redeployments)
.EXAMPLE
    .\deploy.ps1 -Stage dev -Region ap-south-1
    .\deploy.ps1 -Stage prod -OpenAIKey "sk-..." 
#>

param(
    [ValidateSet("dev", "prod")]
    [string]$Stage = "dev",

    [string]$Region = "ap-south-1",

    [string]$StackName = "docsetu-ai",

    [string]$OpenAIKey = "",

    [switch]$SkipBuild
)

# ============================================================================
# CONFIGURATION
# ============================================================================
$ErrorActionPreference = "Stop"
$script:ExitCode = 0
$S3BucketName = "$StackName-sam-artifacts-$Stage-$Region"
$SSMPrefix = "/$StackName/$Stage"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
function Write-Banner {
    $banner = @"

    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║           ██████╗  ██████╗  ██████╗███████╗███████╗████████╗║
    ║           ██╔══██╗██╔═══██╗██╔════╝██╔════╝██╔════╝╚══██╔══╝║
    ║           ██║  ██║██║   ██║██║     ███████╗█████╗     ██║   ║
    ║           ██║  ██║██║   ██║██║     ╚════██║██╔══╝     ██║   ║
    ║           ██████╔╝╚██████╔╝╚██████╗███████║███████╗   ██║   ║
    ║           ╚═════╝  ╚═════╝  ╚═════╝╚══════╝╚══════╝   ╚═╝   ║
    ║                                                              ║
    ║              DocSetu AI - Serverless Deployment               ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝

"@
    Write-Host $banner -ForegroundColor Cyan
    Write-Host "  Stage:      $Stage" -ForegroundColor White
    Write-Host "  Region:     $Region" -ForegroundColor White
    Write-Host "  Stack:      $StackName" -ForegroundColor White
    Write-Host "  Timestamp:  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor White
    Write-Host ""
    Write-Host "  ─────────────────────────────────────────────────────────" -ForegroundColor DarkGray
    Write-Host ""
}

function Write-StepHeader([string]$Step, [string]$Description) {
    Write-Host ""
    Write-Host "  [$Step] $Description" -ForegroundColor Cyan
    Write-Host "  ────────────────────────────────────────" -ForegroundColor DarkGray
}

function Write-Success([string]$Message) {
    Write-Host "  ✓ $Message" -ForegroundColor Green
}

function Write-Error([string]$Message) {
    Write-Host "  ✗ $Message" -ForegroundColor Red
}

function Write-Warning([string]$Message) {
    Write-Host "  ⚠ $Message" -ForegroundColor Yellow
}

function Write-Info([string]$Message) {
    Write-Host "  → $Message" -ForegroundColor Gray
}

function Test-Command([string]$Command) {
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

function New-RandomSecret([int]$Length = 64) {
    $chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*"
    $secret = -join (1..$Length | ForEach-Object { $chars[(Get-Random -Maximum $chars.Length)] })
    return $secret
}

# ============================================================================
# STEP 1: PRE-FLIGHT CHECKS
# ============================================================================
function Invoke-PreflightChecks {
    Write-StepHeader "1/6" "Pre-flight Checks"
    
    $allPassed = $true

    # Check AWS CLI
    if (Test-Command "aws") {
        $awsVersion = (aws --version 2>&1) -join ""
        Write-Success "AWS CLI installed: $awsVersion"
    } else {
        Write-Error "AWS CLI not found. Install from https://aws.amazon.com/cli/"
        $allPassed = $false
    }

    # Check SAM CLI
    if (Test-Command "sam") {
        $samVersion = (sam --version 2>&1) -join ""
        Write-Success "SAM CLI installed: $samVersion"
    } else {
        Write-Error "SAM CLI not found. Install from https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"
        $allPassed = $false
    }

    # Check Python 3.11
    $python311 = $null
    foreach ($cmd in @("python3.11", "python3", "python")) {
        if (Test-Command $cmd) {
            $version = & $cmd --version 2>&1
            if ($version -match "3\.11") {
                $python311 = $cmd
                Write-Success "Python 3.11 found: $version ($cmd)"
                break
            }
        }
    }
    if (-not $python311) {
        Write-Error "Python 3.11 not found. Install from https://www.python.org/downloads/"
        $allPassed = $false
    }

    # Check AWS credentials
    try {
        $identity = aws sts get-caller-identity --region $Region 2>&1 | ConvertFrom-Json
        Write-Success "AWS credentials configured: Account $($identity.Account)"
    } catch {
        Write-Error "AWS credentials not configured. Run 'aws configure' first."
        $allPassed = $false
    }

    # Validate parameters
    if ($Stage -notin @("dev", "prod")) {
        Write-Error "Invalid stage '$Stage'. Must be 'dev' or 'prod'."
        $allPassed = $false
    } else {
        Write-Success "Parameters validated (Stage=$Stage, Region=$Region)"
    }

    if (-not $allPassed) {
        Write-Host ""
        Write-Error "Pre-flight checks failed. Fix the issues above and retry."
        exit 1
    }

    Write-Host ""
    Write-Success "All pre-flight checks passed!"
}

# ============================================================================
# STEP 2: S3 BUCKET FOR SAM ARTIFACTS
# ============================================================================
function Invoke-CreateS3Bucket {
    Write-StepHeader "2/6" "S3 Artifact Bucket"

    try {
        # Check if bucket exists
        $bucketExists = $false
        try {
            aws s3api head-bucket --bucket $S3BucketName --region $Region 2>&1 | Out-Null
            $bucketExists = $true
        } catch {
            $bucketExists = $false
        }

        if ($bucketExists) {
            Write-Success "S3 bucket already exists: $S3BucketName"
        } else {
            Write-Info "Creating S3 bucket: $S3BucketName"
            
            if ($Region -eq "us-east-1") {
                aws s3api create-bucket `
                    --bucket $S3BucketName `
                    --region $Region 2>&1 | Out-Null
            } else {
                aws s3api create-bucket `
                    --bucket $S3BucketName `
                    --region $Region `
                    --create-bucket-configuration "LocationConstraint=$Region" 2>&1 | Out-Null
            }

            # Enable versioning
            aws s3api put-bucket-versioning `
                --bucket $S3BucketName `
                --versioning-configuration Status=Enabled `
                --region $Region 2>&1 | Out-Null

            # Block public access
            aws s3api put-public-access-block `
                --bucket $S3BucketName `
                --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" `
                --region $Region 2>&1 | Out-Null

            Write-Success "S3 bucket created with versioning and public access blocked"
        }
    } catch {
        Write-Error "Failed to create S3 bucket: $_"
        Write-Warning "You may need to choose a different bucket name or check permissions."
        exit 2
    }
}

# ============================================================================
# STEP 3: SECRETS MANAGEMENT (SSM PARAMETER STORE)
# ============================================================================
function Invoke-StoreSecrets {
    Write-StepHeader "3/6" "Secrets Management (SSM Parameter Store)"

    try {
        # Generate JWT secret
        $jwtSecret = New-RandomSecret -Length 64
        
        # Check if JWT secret already exists
        $existingSecret = $null
        try {
            $existingSecret = aws ssm get-parameter `
                --name "$SSMPrefix/jwt-secret" `
                --with-decryption `
                --region $Region 2>&1 | ConvertFrom-Json
        } catch {
            $existingSecret = $null
        }

        if ($existingSecret) {
            Write-Success "JWT secret already exists in SSM (not overwriting)"
        } else {
            aws ssm put-parameter `
                --name "$SSMPrefix/jwt-secret" `
                --value $jwtSecret `
                --type SecureString `
                --description "DocSetu AI JWT signing secret ($Stage)" `
                --region $Region 2>&1 | Out-Null
            Write-Success "JWT secret generated and stored in SSM: $SSMPrefix/jwt-secret"
        }

        # Store OpenAI key if provided
        if ($OpenAIKey) {
            aws ssm put-parameter `
                --name "$SSMPrefix/openai-api-key" `
                --value $OpenAIKey `
                --type SecureString `
                --description "OpenAI API key for DocSetu AI ($Stage)" `
                --overwrite `
                --region $Region 2>&1 | Out-Null
            Write-Success "OpenAI API key stored in SSM: $SSMPrefix/openai-api-key"
        } else {
            Write-Warning "No OpenAI key provided. AI features will be disabled."
            Write-Info "Add later with: .\deploy.ps1 -OpenAIKey 'sk-...'"
        }

        # Store stage config
        aws ssm put-parameter `
            --name "$SSMPrefix/stage" `
            --value $Stage `
            --type String `
            --description "DocSetu AI deployment stage" `
            --overwrite `
            --region $Region 2>&1 | Out-Null
        Write-Success "Stage configuration stored in SSM"

    } catch {
        Write-Error "Failed to store secrets in SSM: $_"
        Write-Warning "Check IAM permissions for ssm:PutParameter"
        exit 3
    }
}

# ============================================================================
# STEP 4: SAM BUILD
# ============================================================================
function Invoke-SamBuild {
    Write-StepHeader "4/6" "SAM Build"

    if ($SkipBuild) {
        Write-Warning "Skipping build (--SkipBuild flag set)"
        return
    }

    try {
        Write-Info "Building with SAM (Python 3.11 runtime)..."
        Write-Info "This may take a few minutes on first build..."

        $buildOutput = sam build `
            --use-container `
            --runtime python3.11 `
            --region $Region 2>&1

        if ($LASTEXITCODE -ne 0) {
            # Try without container if Docker is not available
            Write-Warning "Container build failed. Trying native build..."
            $buildOutput = sam build `
                --runtime python3.11 `
                --region $Region 2>&1

            if ($LASTEXITCODE -ne 0) {
                throw "SAM build failed: $buildOutput"
            }
        }

        Write-Success "SAM build completed successfully"
    } catch {
        Write-Error "SAM build failed: $_"
        Write-Warning "Common fixes:"
        Write-Warning "  - Ensure template.yaml exists in the current directory"
        Write-Warning "  - Check requirements.txt for invalid packages"
        Write-Warning "  - Install Docker for container-based builds"
        exit 4
    }
}

# ============================================================================
# STEP 5: SAM DEPLOY
# ============================================================================
function Invoke-SamDeploy {
    Write-StepHeader "5/6" "SAM Deploy"

    try {
        Write-Info "Deploying stack: $StackName-$Stage to $Region..."

        $deployParams = @(
            "--stack-name", "$StackName-$Stage",
            "--s3-bucket", $S3BucketName,
            "--s3-prefix", "sam-packages",
            "--region", $Region,
            "--capabilities", "CAPABILITY_IAM CAPABILITY_AUTO_EXPAND",
            "--no-confirm-changeset",
            "--no-fail-on-empty-changeset",
            "--parameter-overrides",
            "Stage=$Stage",
            "JwtSecretParam=$SSMPrefix/jwt-secret",
            "OpenAIKeyParam=$SSMPrefix/openai-api-key"
        )

        $deployOutput = sam deploy @deployParams 2>&1

        if ($LASTEXITCODE -ne 0) {
            throw "SAM deploy failed: $deployOutput"
        }

        Write-Success "Deployment initiated successfully"

        # Wait for stack completion
        Write-Info "Waiting for stack to reach stable state..."
        aws cloudformation wait stack-create-complete `
            --stack-name "$StackName-$Stage" `
            --region $Region 2>&1 | Out-Null

        if ($LASTEXITCODE -ne 0) {
            # Try update-complete if create-complete fails (stack already existed)
            aws cloudformation wait stack-update-complete `
                --stack-name "$StackName-$Stage" `
                --region $Region 2>&1 | Out-Null
        }

        Write-Success "Stack deployment complete!"

    } catch {
        Write-Error "Deployment failed: $_"
        Write-Warning ""
        Write-Warning "Rollback Information:"
        Write-Warning "  - Check CloudFormation console for detailed errors"
        Write-Warning "  - Run: aws cloudformation describe-stack-events --stack-name $StackName-$Stage --region $Region"
        Write-Warning "  - To delete failed stack: .\destroy.ps1 -Stage $Stage -Region $Region"
        exit 5
    }
}

# ============================================================================
# STEP 6: POST-DEPLOYMENT
# ============================================================================
function Invoke-PostDeploy {
    Write-StepHeader "6/6" "Post-Deployment"

    try {
        # Get stack outputs
        $outputs = aws cloudformation describe-stacks `
            --stack-name "$StackName-$Stage" `
            --region $Region `
            --query "Stacks[0].Outputs" 2>&1 | ConvertFrom-Json

        $apiUrl = ($outputs | Where-Object { $_.OutputKey -eq "ApiUrl" }).OutputValue
        $bucketName = ($outputs | Where-Object { $_.OutputKey -eq "DocumentBucket" }).OutputValue
        $userPoolId = ($outputs | Where-Object { $_.OutputKey -eq "UserPoolId" }).OutputValue

        # Fallback if outputs not found
        if (-not $apiUrl) {
            $apiUrl = "https://<api-id>.execute-api.$Region.amazonaws.com/$Stage"
            Write-Warning "Could not retrieve API URL from stack outputs. Check CloudFormation console."
        }

        Write-Host ""
        Write-Host "  ╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "  ║              🎉 DEPLOYMENT SUCCESSFUL! 🎉                    ║" -ForegroundColor Green
        Write-Host "  ╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
        Write-Host ""
        Write-Host "  ┌─────────────────────────────────────────────────────────────┐" -ForegroundColor White
        Write-Host "  │ Stack Outputs                                               │" -ForegroundColor White
        Write-Host "  ├─────────────────────────────────────────────────────────────┤" -ForegroundColor White
        Write-Host "  │ API URL:        $apiUrl" -ForegroundColor White
        if ($bucketName) {
            Write-Host "  │ S3 Bucket:      $bucketName" -ForegroundColor White
        }
        if ($userPoolId) {
            Write-Host "  │ User Pool:      $userPoolId" -ForegroundColor White
        }
        Write-Host "  │ Region:         $Region" -ForegroundColor White
        Write-Host "  │ Stage:          $Stage" -ForegroundColor White
        Write-Host "  └─────────────────────────────────────────────────────────────┘" -ForegroundColor White

        # Quick-start guide
        Write-Host ""
        Write-Host "  ┌─────────────────────────────────────────────────────────────┐" -ForegroundColor Cyan
        Write-Host "  │ Quick-Start Guide                                           │" -ForegroundColor Cyan
        Write-Host "  ├─────────────────────────────────────────────────────────────┤" -ForegroundColor Cyan
        Write-Host "  │                                                             │" -ForegroundColor Cyan
        Write-Host "  │ 1. Test Health Endpoint:                                    │" -ForegroundColor Cyan
        Write-Host "  │    curl $apiUrl/health" -ForegroundColor Yellow
        Write-Host "  │                                                             │" -ForegroundColor Cyan
        Write-Host "  │ 2. Register a User:                                         │" -ForegroundColor Cyan
        Write-Host "  │    curl -X POST $apiUrl/auth/register \" -ForegroundColor Yellow
        Write-Host "  │      -H 'Content-Type: application/json' \" -ForegroundColor Yellow
        Write-Host "  │      -d '{""email"":""test@example.com"",""password"":""Test123!""}'" -ForegroundColor Yellow
        Write-Host "  │                                                             │" -ForegroundColor Cyan
        Write-Host "  │ 3. Login:                                                   │" -ForegroundColor Cyan
        Write-Host "  │    curl -X POST $apiUrl/auth/login \" -ForegroundColor Yellow
        Write-Host "  │      -H 'Content-Type: application/json' \" -ForegroundColor Yellow
        Write-Host "  │      -d '{""email"":""test@example.com"",""password"":""Test123!""}'" -ForegroundColor Yellow
        Write-Host "  │                                                             │" -ForegroundColor Cyan
        Write-Host "  └─────────────────────────────────────────────────────────────┘" -ForegroundColor Cyan

        # Frontend .env update
        Write-Host ""
        Write-Host "  ┌─────────────────────────────────────────────────────────────┐" -ForegroundColor Magenta
        Write-Host "  │ Frontend Configuration                                      │" -ForegroundColor Magenta
        Write-Host "  ├─────────────────────────────────────────────────────────────┤" -ForegroundColor Magenta
        Write-Host "  │                                                             │" -ForegroundColor Magenta
        Write-Host "  │ Update your frontend .env file:                             │" -ForegroundColor Magenta
        Write-Host "  │                                                             │" -ForegroundColor Magenta
        Write-Host "  │   VITE_API_URL=$apiUrl" -ForegroundColor Yellow
        Write-Host "  │   VITE_STAGE=$Stage" -ForegroundColor Yellow
        Write-Host "  │   VITE_REGION=$Region" -ForegroundColor Yellow
        if ($userPoolId) {
            Write-Host "  │   VITE_USER_POOL_ID=$userPoolId" -ForegroundColor Yellow
        }
        Write-Host "  │                                                             │" -ForegroundColor Magenta
        Write-Host "  └─────────────────────────────────────────────────────────────┘" -ForegroundColor Magenta
        Write-Host ""

    } catch {
        Write-Warning "Could not retrieve all stack outputs: $_"
        Write-Info "Check AWS CloudFormation console for deployment details."
    }
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================
try {
    Write-Banner
    Invoke-PreflightChecks
    Invoke-CreateS3Bucket
    Invoke-StoreSecrets
    Invoke-SamBuild
    Invoke-SamDeploy
    Invoke-PostDeploy

    Write-Host ""
    Write-Success "DocSetu AI deployment completed successfully! 🚀"
    Write-Host ""
    exit 0

} catch {
    Write-Host ""
    Write-Error "Deployment failed with an unexpected error:"
    Write-Error "$_"
    Write-Host ""
    Write-Warning "For troubleshooting:"
    Write-Warning "  1. Check CloudFormation events in AWS Console"
    Write-Warning "  2. Review CloudWatch Logs for Lambda errors"
    Write-Warning "  3. Run with -Verbose for detailed output"
    Write-Warning "  4. To rollback: .\destroy.ps1 -Stage $Stage -Region $Region"
    Write-Host ""
    exit 99
}
