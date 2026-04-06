# IAM Setup for GitHub Actions (OIDC)

One-time setup. No long-lived AWS credentials are stored anywhere.

## Before you start: two values you need

**AWS Account ID** — the 12-digit ID of the account where you will create the IAM role. Find it
in the AWS console top-right menu, or run:
```bash
aws sts get-caller-identity --query Account --output text
```

**S3 Bucket** — Create a new bucket dedicated to condenser automated runs. Two constraints:

- Must be in **us-west-1** (Rigetti Ankaa-3's region — Braket writes results to S3 in the
  device's region).
- **Must start with `amazon-braket-`** — Braket's service-linked role enforces this naming
  convention and will reject any bucket name that doesn't match.

Use an admin-level AWS credential to create it:

```bash
aws s3api create-bucket \
  --bucket amazon-braket-YOUR_ORG-condenser \
  --region us-west-1 \
  --create-bucket-configuration LocationConstraint=us-west-1
```

Do **not** rename or touch any existing Braket result prefixes — historical notebooks may still
write there. The new bucket is only for automated condenser runs going forward.

Edit `iam-policy.json` to replace `YOUR_BRAKET_RESULTS_BUCKET` with your chosen bucket name
before running Step 3.

---

## Steps

### 1. Add GitHub as an OIDC provider in AWS (once per account)

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

If the provider already exists in your account, skip this step.

### 2. Create the IAM role

Edit `iam-trust-policy.json` — replace `YOUR_ACCOUNT_ID` with your 12-digit AWS account ID
(the same one from the `sts get-caller-identity` command above).

```bash
aws iam create-role \
  --role-name condenser-github-actions \
  --assume-role-policy-document file://iam-trust-policy.json
```

### 3. Attach the permissions policy

Edit `iam-policy.json` — replace `YOUR_BRAKET_RESULTS_BUCKET` with the S3 bucket name.

```bash
aws iam put-role-policy \
  --role-name condenser-github-actions \
  --policy-name condenser-braket-policy \
  --policy-document file://iam-policy.json
```

### 4. Save the role ARN as a GitHub secret

```bash
aws iam get-role --role-name condenser-github-actions --query Role.Arn --output text
```

Go to: GitHub repo → Settings → Environments → `quantum-production` → Add secret
- Name: `AWS_ROLE_ARN`
- Value: the ARN from above (e.g. `arn:aws:iam::123456789012:role/condenser-github-actions`)

### 5. Save the bucket name as a GitHub Actions variable

This is *not* a secret — bucket names aren't sensitive. Go to:
GitHub repo → Settings → Variables → Actions → New repository variable
- Name: `BRAKET_RESULTS_BUCKET`
- Value: your S3 bucket name

This is the single source of truth for the bucket name in the workflow. The IAM policy
(step 3 above) must reference the same bucket, but it is only edited once at setup time.

---

## GitHub Environment setup

In the repo settings (Settings → Environments → New environment):

1. Name: `quantum-production`
2. **Deployment branches**: restrict to `main` only — this prevents fork PRs from ever
   accessing secrets in this environment
3. **Required reviewers** (optional but recommended for manual runs): add yourself so
   `workflow_dispatch` triggers require human approval before spending QPU credits
