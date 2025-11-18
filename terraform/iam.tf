# 1. Fargate Execution Role (Infrastructure: Pull Images, Get Secrets, Write Logs)
resource "aws_iam_policy" "fargate_exec_policy_v3" {
  name        = "MISO-Fargate-Exec-Policy-v3"
  description = "Infrastructure permissions: ECR, Logs, Secrets"
  policy      = jsonencode({
    Version   = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ],
        Resource = "*"
      },
      {
        Effect   = "Allow",
        Action   = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = "arn:aws:logs:us-east-1:356206423360:log-group:/ecs/miso-worker-task:*"
      },
      {
        Effect   = "Allow",
        Action   = "secretsmanager:GetSecretValue",
        Resource = [
          "arn:aws:secretsmanager:us-east-1:356206423360:secret:miso/github_pat-aCUa8g",
          "arn:aws:secretsmanager:us-east-1:356206423360:secret:miso/gemini_api_key-sJkRuG",
          "arn:aws:secretsmanager:us-east-1:356206423360:secret:miso/webhook_secret-lxlx5U"
        ]
      }
    ]
  })
}

resource "aws_iam_role" "fargate_exec_role_v2" {
  name               = "miso-fargate-exec-role-v2"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "ecs-tasks.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "attach_v3_policy" {
  role       = aws_iam_role.fargate_exec_role_v2.name
  policy_arn = aws_iam_policy.fargate_exec_policy_v3.arn
}

# 2. Fargate Task Role (Application: SQS, S3, etc.)
resource "aws_iam_role" "fargate_task_role_v2" {
  name = "miso-fargate-task-role-v2"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "ecs-tasks.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })
}

# --- THIS IS THE MISSING PIECE ---
resource "aws_iam_policy" "worker_app_policy" {
  name        = "MISO-Worker-App-Policy"
  description = "Application permissions: SQS Access"
  policy      = jsonencode({
    Version   = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:ChangeMessageVisibility"
        ],
        Resource = "arn:aws:sqs:us-east-1:356206423360:miso_job_queue"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_worker_policy" {
  role       = aws_iam_role.fargate_task_role_v2.name
  policy_arn = aws_iam_policy.worker_app_policy.arn
}
