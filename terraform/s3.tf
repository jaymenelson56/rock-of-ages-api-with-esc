# -----------------------------
# Reference existing image bucket (managed in backend repo)
# -----------------------------

data "aws_s3_bucket" "images" {
  bucket = var.image_storage_bucket
}

# CORS configuration (REQUIRED for presigned URL uploads from browser)
resource "aws_s3_bucket_cors_configuration" "images" {
  bucket = data.aws_s3_bucket.images.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["PUT", "POST", "GET"]
    allowed_origins = ["*"] 
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# Bucket policy allowing ECS task role
resource "aws_s3_bucket_policy" "images" {
  bucket = data.aws_s3_bucket.images.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowECSTaskRole"
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.ecs_task_role.arn
        }
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          data.aws_s3_bucket.images.arn,
          "${data.aws_s3_bucket.images.arn}/*"
        ]
      }
    ]
  })
}