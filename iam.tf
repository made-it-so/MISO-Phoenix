# 1. Execution Role (Infrastructure)
resource "aws_iam_policy" "fargate_exec_policy_v3" {
  name = "MISO-Fargate-Exec-Policy-v3"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = ["ecr:*", "logs:*", "secretsmanager:GetSecretValue"],
        Resource = "*"
      },
      {
        # CORRECTED LINE: Using 
        Effect   = "Allow",
        Action   = ["logs:CreateLogStream", "logs:PutLogEvents"],
        Resource = "arn:aws:logs::356206423360:log-group:/ecs/miso-worker-task:*"
      }
    ]
  })
}

resource "aws_iam_role" "fargate_exec_role_v2" {
  name = "miso-fargate-exec-role-v2"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{ Effect = "Allow", Principal = { Service = "ecs-tasks.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}

resource "aws_iam_role_policy_attachment" "attach_v3_policy" {
  role = aws_iam_role.fargate_exec_role_v2.name
  policy_arn = aws_iam_policy.fargate_exec_policy_v3.arn
}

# 2. Task Role (Application: SQS and DynamoDB)
resource "aws_iam_role" "fargate_task_role_v2" {
  name = "miso-fargate-task-role-v2"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{ Effect = "Allow", Principal = { Service = "ecs-tasks.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}

# 3. Application Policy (SQS + DynamoDB)
resource "aws_iam_policy" "worker_app_policy" {
  name = "MISO-Worker-App-Policy"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = ["sqs:*"],
        # CORRECTED LINE: Using 
        Resource = "arn:aws:sqs::356206423360:miso_job_queue"
      },
      {
        Effect = "Allow",
        Action = ["dynamodb:*"],
        Resource = "*" 
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_worker_policy" {
  role = aws_iam_role.fargate_task_role_v2.name
  policy_arn = aws_iam_policy.worker_app_policy.arn
}
