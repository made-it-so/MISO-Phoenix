resource "aws_ecs_service" "worker_service_iac" {
  name            = "miso-worker-service-iac"
  cluster         = data.aws_ecs_cluster.main.id
  launch_type     = "FARGATE"
  desired_count   = 1

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

resource "aws_appautoscaling_target" "worker_scaling_target" {
  max_capacity       = 10
  min_capacity       = 1
  resource_id        = "service/MISO-Cluster-Elastic/miso-worker-service-iac"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
  depends_on         = [aws_ecs_service.worker_service_iac]
}

resource "aws_appautoscaling_policy" "worker_scaling_policy" {
  name               = "miso-worker-sqs-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.worker_scaling_target.resource_id
  scalable_dimension = aws_appautoscaling_target.worker_scaling_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.worker_scaling_target.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value = 3.0
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

# --- FIXED TASK DEFINITION ---
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
      # ADDED: Environment Variables for SQS
      environment = [
        {
          name  = "MISO_SQS_QUEUE_URL",
          value = "https://queue.amazonaws.com/356206423360/miso_job_queue"
        },
        {
          name  = "SQS_QUEUE_URL",
          value = "https://queue.amazonaws.com/356206423360/miso_job_queue"
        }
      ],
      # ADDED: Secrets for API Keys
      secrets = [
        {
          name      = "GEMINI_API_KEY",
          valueFrom = "arn:aws:secretsmanager:us-east-1:356206423360:secret:miso/gemini_api_key-sJkRuG"
        }
      ],
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
