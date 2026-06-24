resource "aws_ecr_repository" "api" {
  name                 = "rock-of-ages-api"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
}
