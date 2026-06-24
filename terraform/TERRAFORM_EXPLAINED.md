# Terraform Explained

This document explains every Terraform file in this project line by line.

---

## What is Terraform, briefly?

Terraform is a tool that lets you describe your cloud infrastructure as code. Instead of clicking through the AWS console, you write `.tf` files and Terraform figures out what to create, update, or destroy. The files here collectively define all the AWS resources needed to run the Rock of Ages API in the cloud.

---

## main.tf — The entry point

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```
- This tells Terraform: "I need the AWS plugin (called a *provider*)."
- `hashicorp/aws` is the official AWS plugin published by HashiCorp (the company that makes Terraform).
- `~> 5.0` means "any 5.x version." The `~>` operator locks the major version so a 6.0 breaking change can't sneak in.

```hcl
provider "aws" {
  region = var.aws_region
}
```
- This configures the AWS provider to deploy everything into the region defined in `variables.tf` (defaults to `us-east-2`, which is Ohio).
- `var.aws_region` is how you reference a variable — more on those next.

---

## variables.tf — Configurable inputs

Think of these as function parameters for your whole infrastructure. Instead of hardcoding values everywhere, you define them once here and reference them with `var.<name>`.

```hcl
variable "aws_region" {
  default = "us-east-2"
}
```
- Defaults to Ohio. You could override this when running `terraform apply` if you wanted a different region.

```hcl
variable "image_storage_bucket" {
  default = "<your-storage-bucket-name>"
}
```
- The name of the S3 bucket that stores rock images. This bucket is managed in a *separate* bootstrap project, so Terraform doesn't create it — it just references it.

```hcl
variable "db_username" { default = "rockadmin" }
variable "db_password" { sensitive = true }
variable "db_name"     { default = "rockofages" }
```
- Credentials for the PostgreSQL database. `db_password` has no default and is marked `sensitive = true`, which means Terraform won't print it in logs. You'd pass it in at deploy time (e.g. via a GitHub Actions secret).

---

## backend.tf — Where Terraform stores its state

Terraform keeps a file called `terraform.tfstate` that tracks what it has already built. By default that lives on your laptop, which is a problem for a team or CI/CD pipeline. This file moves it to S3.

```hcl
terraform {
  backend "s3" {
    bucket         = "<your-state-bucket-name>"
    key            = "api/terraform.tfstate"
    region         = "us-east-2"
    dynamodb_table = "rock-of-ages-terraform-locks"
    encrypt        = true
  }
}
```
- `bucket` — the S3 bucket to store the state file in.
- `key` — the path within that bucket. Think of it like a filename: `api/terraform.tfstate`.
- `dynamodb_table` — a DynamoDB table used for *locking*. If two people (or two CI jobs) run `terraform apply` at the same time, the lock prevents them from corrupting the state file by racing each other.
- `encrypt = true` — the state file is encrypted at rest in S3, important because it contains database passwords.

---

## ecr.tf — Docker image registry

```hcl
resource "aws_ecr_repository" "api" {
  name                 = "rock-of-ages-api"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
}
```
- **ECR** (Elastic Container Registry) is AWS's private Docker Hub. Your GitHub Actions workflow builds a Docker image and pushes it here.
- `image_tag_mutability = "MUTABLE"` means you can overwrite the `latest` tag. The alternative would be `IMMUTABLE`, which forces a unique tag every push.
- `force_delete = true` means if you run `terraform destroy`, it will delete the repo even if it still has images in it. Useful for demos, risky in production.

---

## network.tf — VPC, security groups, and the load balancer

This is the most complex file. It defines the networking layer.

### VPC and Subnets

```hcl
data "aws_vpc" "default" { default = true }
data "aws_subnets" "default" {
  filter { name = "vpc-id", values = [data.aws_vpc.default.id] }
}
```
- `data` blocks are *read-only lookups* — they don't create anything, they just fetch existing AWS resources.
- Every AWS account comes with a default VPC (a virtual private network). This grabs it by looking for the one marked `default = true`.
- Then it fetches all the subnets inside that VPC. Subnets are subdivisions of the network — AWS creates one per availability zone by default.

### Security Group: ECS

```hcl
resource "aws_security_group" "ecs_sg" {
  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }
  egress { ... cidr_blocks = ["0.0.0.0/0"] }
}
```
- A security group is a firewall rule set attached to a resource.
- This one controls traffic to the Django containers. It says: **only accept inbound traffic on port 8000, and only if it's coming from the load balancer** (referenced by ID, not by IP). The containers are never directly reachable from the internet.
- The `egress` block (`0.0.0.0/0`, port 0-0, protocol `-1`) means "allow all outbound traffic." Containers need to reach out to ECR to pull images, to RDS for the database, and to S3 for images.

### Security Group: ALB

```hcl
resource "aws_security_group" "alb_sg" {
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```
- The load balancer's firewall. It accepts HTTP (port 80) from anywhere on the internet (`0.0.0.0/0` = all IPs).

### Security Group: RDS

```hcl
resource "aws_security_group" "rds_sg" {
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # open for workshop/demo purposes
  }
}
```
- Controls traffic to the PostgreSQL database. Port 5432 is the standard Postgres port.
- `0.0.0.0/0` means anyone can attempt to connect. The comment calls this out as intentional for a workshop/demo. In a real production app you'd lock this down to only the ECS security group.

### DB Subnet Group

```hcl
resource "aws_db_subnet_group" "rock_of_ages" {
  subnet_ids = data.aws_subnets.default.ids
}
```
- RDS requires you to specify which subnets it can live in. This groups all the default subnets together and assigns them to the database.

### Application Load Balancer

```hcl
resource "aws_lb" "application_load_balancer" {
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = data.aws_subnets.default.ids
}
```
- `internal = false` means it faces the public internet (has a public DNS name).
- It sits across all the default subnets (multiple availability zones), which gives it high availability.

### Target Group

```hcl
resource "aws_lb_target_group" "api_tg" {
  port        = 8000
  target_type = "ip"
  health_check {
    path                = "/health"
    matcher             = "200"
    interval            = 30
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}
```
- A target group is the list of backends the load balancer can route to. `target_type = "ip"` is required for Fargate (containers don't have fixed EC2 instance IDs).
- The health check hits `GET /health` every 30 seconds. If a container returns HTTP 200 twice in a row it's considered healthy. If it fails 3 times in a row it's removed from rotation. The `/health` endpoint in `rockapi/views/health_check.py` exists specifically for this.

### ALB Listener

```hcl
resource "aws_lb_listener" "http_listener" {
  port     = 80
  protocol = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api_tg.arn
  }
}
```
- This wires it together: the load balancer listens on port 80 and forwards all traffic to the target group (which contains the ECS containers).

---

## rds.tf — The PostgreSQL database

```hcl
resource "aws_db_instance" "rock_of_ages" {
  engine         = "postgres"
  instance_class = "db.t4g.micro"
  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp2"
```
- Creates a managed PostgreSQL database.
- `db.t4g.micro` is the smallest (cheapest) RDS tier — 2 vCPUs, 1 GB RAM.
- Starts at 20 GB of storage and can autoscale up to 100 GB.
- `gp2` is a general-purpose SSD storage type.

```hcl
  publicly_accessible     = true
  skip_final_snapshot     = true
  backup_retention_period = 1
  deletion_protection     = false
```
- `publicly_accessible = true` — the database has a public endpoint. The security group still controls who can actually connect, but in production you'd typically keep this `false`.
- `skip_final_snapshot = true` — when you destroy this, don't take a backup snapshot first. Fine for demos, would be dangerous for real data.
- `backup_retention_period = 1` — keep 1 day of automated backups.
- `deletion_protection = false` — allows `terraform destroy` to delete the database.

---

## ecs.tf — The containerized app

### ECS Cluster

```hcl
resource "aws_ecs_cluster" "main" {
  name = "rock-of-ages-cluster"
}
```
- A cluster is just a logical grouping of containers. Fargate handles the underlying servers, so the cluster itself is almost just a name.

### Task Definition

```hcl
resource "aws_ecs_task_definition" "api" {
  family                   = "rock-of-ages-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"   # 0.25 vCPU
  memory                   = "512"   # 0.5 GB
```
- A task definition is a blueprint for a container — like a `docker-compose.yml` in AWS form.
- `awsvpc` gives each task its own network interface and IP address.
- `FARGATE` means AWS manages the underlying EC2 instances for you.

```hcl
  container_definitions = jsonencode([{
    name  = "api"
    image = "${aws_ecr_repository.api.repository_url}:latest"
    portMappings = [{ containerPort = 8000 }]
    logConfiguration = {
      logDriver = "awslogs"
      options = { "awslogs-group" = "/ecs/rock-of-ages-api", ... }
    }
    environment = [
      { name = "DB_HOST",                 value = aws_db_instance.rock_of_ages.address },
      { name = "DB_NAME",                 value = ... },
      { name = "DB_USER",                 value = ... },
      { name = "DB_PASSWORD",             value = var.db_password },
      { name = "AWS_STORAGE_BUCKET_NAME", value = var.image_storage_bucket },
      { name = "AWS_REGION",              value = var.aws_region }
    ]
  }])
```
- `image` — tells ECS exactly where to pull the Docker image from (your ECR repo, `latest` tag).
- `logConfiguration` — sends all container stdout/stderr to CloudWatch Logs under `/ecs/rock-of-ages-api`.
- `environment` — injects all the database credentials and S3 config as environment variables into the container. This is how Django's `settings.py` reads `DB_HOST`, `DB_NAME`, etc. at runtime. Terraform automatically wires the RDS address in here.

### CloudWatch Log Group

```hcl
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/rock-of-ages-api"
  retention_in_days = 7
}
```
- Creates the log group in CloudWatch where container logs land. Retains them for 7 days to keep costs low.

### ECS Service

```hcl
resource "aws_ecs_service" "api" {
  desired_count   = 2
  launch_type     = "FARGATE"
  load_balancer {
    target_group_arn = aws_lb_target_group.api_tg.arn
    container_port   = 8000
  }
  depends_on = [aws_lb_listener.http_listener]
}
```
- The service is what keeps the task definition *running*. It says "keep 2 copies of this container alive at all times." If one crashes, ECS automatically starts a replacement.
- `depends_on` ensures the load balancer listener exists before ECS tries to register with it.

### IAM Roles

```hcl
resource "aws_iam_role" "ecs_task_execution_role" { ... }
resource "aws_iam_role_policy_attachment" "ecs_task_execution_policy" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}
```
- The *execution role* is used by the ECS agent itself (not your code) to pull the Docker image from ECR and send logs to CloudWatch.
- `AmazonECSTaskExecutionRolePolicy` is a managed AWS policy that grants exactly those permissions.

```hcl
resource "aws_iam_role" "ecs_task_role" { ... }
resource "aws_iam_role_policy" "ecs_task_s3_policy" {
  Action = ["s3:PutObject", "s3:GetObject", "s3:DeleteObject", "s3:ListBucket"]
}
```
- The *task role* is used by your Django code while it runs. This one grants permission to read/write/delete objects in the image storage S3 bucket — which is how `s3_service.py` is authorized to upload rock images.

---

## s3.tf — S3 image bucket configuration

```hcl
data "aws_s3_bucket" "images" {
  bucket = var.image_storage_bucket
}
```
- The bucket already exists (created in a separate bootstrap project), so this is a read-only `data` lookup, not a `resource` creation.

```hcl
resource "aws_s3_bucket_cors_configuration" "images" {
  cors_rule {
    allowed_methods = ["PUT", "POST", "GET"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag"]
  }
}
```
- CORS (Cross-Origin Resource Sharing) must be configured so that a browser (running on a different domain than S3) can upload files directly to S3 using a *presigned URL*. Without this, the browser would be blocked by the same-origin policy.
- `ETag` is exposed so the browser can confirm the upload completed correctly.

```hcl
resource "aws_s3_bucket_policy" "images" {
  Principal = { AWS = aws_iam_role.ecs_task_role.arn }
  Action = ["s3:PutObject", "s3:GetObject", "s3:DeleteObject", "s3:ListBucket"]
}
```
- This attaches a *bucket policy* (a resource-side permission) granting the ECS task role access to the bucket. This works in combination with the IAM role policy from `ecs.tf` — both sides need to agree for access to be granted.

---

## outputs.tf — Values printed after `terraform apply`

```hcl
output "ecr_registry_url" { ... }
output "ecs_cluster_name" { ... }
output "ecs_service_name" { ... }
output "db_host"          { ... }
output "alb_dns_name"     { ... }
```
- After Terraform finishes building everything, it prints these values to the terminal.
- `alb_dns_name` is especially important — it's the public URL your API is reachable at (something like `rock-of-ages-alb-1234567890.us-east-2.elb.amazonaws.com`).
- The GitHub Actions workflows likely use `ecs_cluster_name` and `ecs_service_name` to target the right resources during deployment.

---

## The big picture — how all 7 files connect

```
Internet
  → ALB (network.tf, port 80)
    → ECS containers (ecs.tf, port 8000) ← Docker image from ECR (ecr.tf)
      → RDS PostgreSQL (rds.tf)
      → S3 images bucket (s3.tf)

State stored in S3 + DynamoDB lock (backend.tf)
Configurable values abstracted into variables (variables.tf)
```

Every piece of this infrastructure is version-controlled and reproducible. Running `terraform apply` creates the entire stack from scratch; `terraform destroy` tears it all down. That's the core value of infrastructure as code.
