# --- MISO V7: API Service Integration (Port 8080) ---

# 1. Existing Network Infrastructure
data "aws_vpc" "existing_vpc" {
  id = "vpc-0839683a65fa0c5dc"
}

# 2. Lookup Existing Load Balancer
data "aws_lb" "main" {
  name = "miso-alb-fixed"
}

# 3. Create Target Group for the API Service
resource "aws_lb_target_group" "api_tg" {
  name        = "miso-api-tg-v7"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.existing_vpc.id
  target_type = "ip"

  health_check {
    path                = "/health"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }
}

# 4. Create Listener on Alternative Port 8080 (Conflict Avoidance)
resource "aws_lb_listener" "http_8080" {
  load_balancer_arn = data.aws_lb.main.arn
  port              = "8080"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api_tg.arn
  }
}
