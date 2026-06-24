# GitHub Secrets Setup

This project requires 3 GitHub secrets for the CI/CD workflows to run. Here is how to find each value and add it to your repo.

---

## Where to add secrets

**GitHub repo → Settings → Secrets and variables → Actions → New repository secret**

---

## The 3 secrets

### 1. `OIDC_ROLE_TO_ASSUME`

This is the ARN of the IAM role that GitHub Actions assumes to authenticate with AWS. It uses OIDC (federated identity) instead of static access keys.

**How to find it:**

First, make sure your AWS CLI is configured:
```bash
aws configure
```

Then look up the role:
```bash
aws iam list-roles --query "Roles[?contains(RoleName, 'github') || contains(RoleName, 'GitHub') || contains(RoleName, 'oidc') || contains(RoleName, 'OIDC')].Arn" --output table
```

The value will look like:
```
arn:aws:iam::123456789012:role/github_oidc
```

---

### 2. `AWS_REGION`

The AWS region your infrastructure is deployed to.

**Value:** `us-east-2` (set as the default in `terraform/variables.tf`)

---

### 3. `DB_PASSWORD`

The master password for the RDS PostgreSQL database. This is not a value that exists anywhere yet — you are setting it for the first time. Terraform will use it when it creates the database.

**Rules:**
- At least 8 characters
- Cannot contain `/`, `@`, `"`, or spaces

Pick a strong password and save it in a password manager. There is no way to look this up later — if you lose it you will need to reset it in the AWS console.

---

## Why these secrets exist

| Secret | Used in | Purpose |
|---|---|---|
| `OIDC_ROLE_TO_ASSUME` | All 3 workflows | Authenticates GitHub Actions with AWS |
| `AWS_REGION` | `deploy.yml`, `testBuildPush.yml` | Tells the AWS CLI which region to target |
| `DB_PASSWORD` | `testBuildPush.yml`, `destroy.yml` | Passed to Terraform as `TF_VAR_db_password` to create/destroy the RDS instance |
