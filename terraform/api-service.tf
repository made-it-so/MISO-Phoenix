# 1. Import the existing ALB (Front Door)
data "aws_lb" "main" {
  name = "miso-alb"
}

data "aws_lb_listener" "https" {
  load_balancer_arn = data.aws_lb.main.arn
  port              = 443
}

# 2. Target Group (Where traffic goes)
resource "aws_lb_target_group" "api_targets" {
  name        = "miso-api-targets-iac"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/health"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }
}

# 3. Listener Rule (Route traffic to our new service)
resource "aws_lb_listener_rule" "api_rule" {
  listener_arn = data.aws_lb_listener.https.arn
  priority     = 100 

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api_targets.arn
  }

  condition {
    path_pattern {
      values = ["/*"]
    }
  }
}

# 4. The API Service
resource "aws_ecs_service" "api_service_iac" {
  name            = "miso-api-service-iac"
  cluster         = data.aws_ecs_cluster.main.id
  launch_type     = "FARGATE"
  desired_count   = 1

  task_definition = aws_ecs_task_definition.api_placeholder.arn

  network_configuration {
    subnets         = data.aws_subnets.private.ids
    security_groups = [data.aws_security_group.worker_sg.id] # Reusing SG for now
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api_targets.arn
    container_name   = "miso-api"
    container_port   = 80
  }

  depends_on = [
    aws_lb_listener_rule.api_rule,
    aws_iam_role.fargate_exec_role_v2
  ]
}

# 5. Placeholder Task Definition
resource "aws_ecs_task_definition" "api_placeholder" {
  family                   = "miso-api-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.fargate_exec_role_v2.arn
  task_role_arn            = aws_iam_role.fargate_task_role_v2.arn
  
  container_definitions    = jsonencode([
    {
      name      = "miso-api",
      image     = "356206423360.dkr.ecr.us-east-1.amazonaws.com/miso-api:latest", 
      # Note: We need to build this image next!
      essential = true,
      portMappings = [
        {
          containerPort = 80
          hostPort      = 80
        }
      ],
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.worker_logs.name, # Reuse logs for now
          "awslogs-region"        = "us-east-1",
          "awslogs-stream-prefix" = "api"
        }
      }
    }
  ])
}
