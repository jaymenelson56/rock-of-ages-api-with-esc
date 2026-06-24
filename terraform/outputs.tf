output "ecr_registry_url" {
  value = "${aws_ecr_repository.api.registry_id}.dkr.ecr.${var.aws_region}.amazonaws.com"
}

output "ecs_cluster_name" {
  value       = aws_ecs_cluster.main.name
  description = "Name of the ECS cluster"
}

output "ecs_service_name" {
  value       = aws_ecs_service.api.name
  description = "Name of the ECS service"
}

output "ecr_repository" {
  value = aws_ecr_repository.api.name
}

output "db_host" {
  description = "PostgreSQL database endpoint"
  value       = aws_db_instance.rock_of_ages.address
}

output "db_name" {
  description = "database name"
  value       = aws_db_instance.rock_of_ages.db_name
}

output "db_user" {
  description = "database username"
  value       = aws_db_instance.rock_of_ages.username
}

output "alb_dns_name" {
  value       = aws_lb.application_load_balancer.dns_name
  description = "The DNS name of the Application Load Balancer"
}



