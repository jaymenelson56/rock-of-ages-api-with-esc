resource "aws_db_instance" "rock_of_ages" {
  identifier     = "rock-of-ages-db"
  engine         = "postgres"
  instance_class = "db.t4g.micro"

  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp2"

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  publicly_accessible     = true
  skip_final_snapshot     = true
  backup_retention_period = 1

  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.rock_of_ages.name

  deletion_protection = false

  tags = {
    Name = "rock-of-ages-db"
  }
}

