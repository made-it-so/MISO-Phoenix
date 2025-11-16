resource "aws_ecs_service" "worker_service_iac" {
  name            = "miso-worker-service-iac" # New service name
  cluster         = data.aws_ecs_cluster.main.id
  launch_type     = "FARGATE"
  desired_count   = 1 # We start with 1 worker

  task_definition = aws_ecs_task_definition.worker_placeholder.arn

  network_configuration {
    subnets         = data.aws_subnets.private.ids
    security_groups = [data.aws_security_group.worker_sg.id]
    assign_public_ip = false
  }

  service_connect_configuration {
    enabled = false
  }

  depends_on = [
    aws_iam_role.fargate_exec_role_v2,
    aws_cloudwatch_log_group.worker_logs
  ]
}

# This defines the auto-scaling policy for the new service
resource "aws_appautoscaling_target" "worker_scaling_target" {
  max_capacity       = 10
  min_capacity       = 1
  
  # --- THIS IS THE FIX ---
  # Hard-coding the cluster and service name to avoid dependency failure.
  resource_id        = "service/MISO-Cluster-Elastic/miso-worker-service-iac"
  
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
  
  # Explicit dependency to ensure the service is created first.
  depends_on = [
    aws_ecs_service.worker_service_iac
  ]
}
# --- END FIX ---

resource "aws_appautoscaling_policy" "worker_scaling_policy" {
  name               = "miso-worker-sqs-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.worker_scaling_target.resource_id
  scalable_dimension = aws_appautoscaling_target.worker_scaling_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.worker_scaling_target.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value = 3.0 # The target: 3 messages per worker

    customized_metric_specification {
      metric_name = "ApproximateNumberOfMessagesVisible"
      namespace   = "AWS/SQS"
      statistic   = "Average"
      dimensions {
        name  = "QueueName"
        value = aws_sqs_queue.job_queue.name
      }
    }
  }
}

# This is a "placeholder" task def, required by Terraform.
resource "aws_ecs_task_definition" "worker_placeholder" {
  family                   = "miso-worker-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.fargate_exec_role_v2.arn
  task_role_arn            = aws_iam_role.fargate_task_role_v2.arn
  
  container_definitions    = jsonencode([
    {
      name      = "miso-worker",
      image     = "356206423360.dkr.ecr.us-east-1.amazonaws.com/miso-worker:latest",
      essential = true,
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.worker_logs.name,
          "awslogs-region"        = "us-east-1",
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}
