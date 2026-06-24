
variable "aws_region" {
  description = "AWS region to deploy resources into"
  type        = string
  default     = "us-east-2"
}

variable "image_storage_bucket" {
  description = "Storage bucket for rock images created in backend-bootstrap project"
  type        = string
  default     = "<your-storage-bucket-name>" 
}

variable "db_username" {
  description = "Master DB username"
  type        = string
  default     = "rockadmin"
}

variable "db_password" {
  description = "Master DB password"
  type        = string
  sensitive   = true
}

variable "db_name" {
  description = "Initial database name"
  type        = string
  default     = "rockofages"
}



