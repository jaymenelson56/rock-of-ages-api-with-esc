# Use the default VPC
data "aws_vpc" "default" {
  default = true
}

# Get all default subnets in the default VPC
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Create a security group for ECS tasks
resource "aws_security_group" "ecs_sg" {
  name        = "rock-of-ages-ecs-sg"
  description = "Allow HTTP traffic from ALB to ECS tasks"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description     = "Allow HTTP from ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "rock-of-ages-ecs-sg"
  }
}

# Create a security group for ALB added for load balancing
resource "aws_security_group" "alb_sg" {
  name        = "rock-of-ages-alb-sg"
  description = "Allow HTTP traffic to ALB"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "rock-of-ages-alb-sg"
  }
}

# Create a security group for RDS
resource "aws_security_group" "rds_sg" {
  name        = "rock-of-ages-db-sg"
  description = "Allow PostgreSQL connections for Rock of Ages course"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # open for workshop/demo purposes
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "rock-of-ages-db-sg"
  }
}

# Create an RDS DB Subnet Group using the default subnets
resource "aws_db_subnet_group" "rock_of_ages" {
  name       = "rock-of-ages-subnet-group"
  subnet_ids = data.aws_subnets.default.ids
  tags = {
    Name = "rock-of-ages-db-subnet-group"
  }
}

# load balancer all below 
# Application Load Balancer
resource "aws_lb" "application_load_balancer" {
  name               = "rock-of-ages-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = data.aws_subnets.default.ids

  tags = {
    Name = "rock-of-ages-alb"
  }
}

# Target Group
resource "aws_lb_target_group" "api_tg" {
  name        = "rock-of-ages-api-tg"
  port        = 8000  
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.default.id
  target_type = "ip"

  health_check {
    path                = "/health"  
    protocol            = "HTTP"
    port                = "traffic-port"  
    matcher             = "200"
    interval            = 30  
    timeout             = 10 
    healthy_threshold   = 2
    unhealthy_threshold = 3  
  }

  tags = {
    Name = "rock-of-ages-api-tg"
  }
}
# ALB Listener
resource "aws_lb_listener" "http_listener" {
  load_balancer_arn = aws_lb.application_load_balancer.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api_tg.arn
  }
}

