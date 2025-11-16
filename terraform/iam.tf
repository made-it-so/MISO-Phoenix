# This is the new, definitive IAM policy for the Fargate Execution Role
resource "aws_iam_policy" "fargate_exec_policy_v3" {
  name        = "MISO-Fargate-Exec-Policy-v3"
  description = "Definitive IaC-managed policy for MISO Fargate tasks"
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

# This is the new, definitive IAM Role for Fargate
resource "aws_iam_role" "fargate_exec_role_v2" {
  name               = "miso-fargate-exec-role-v2"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17",
    Statement = [
      {
        Effect    = "Allow",
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        },
        Action    = "sts:AssumeRole"
      }
    ]
  })
}

# This attaches the new policy to the new role
resource "aws_iam_role_policy_attachment" "attach_v3_policy" {
  role       = aws_iam_role.fargate_exec_role_v2.name
  policy_arn = aws_iam_policy.fargate_exec_policy_v3.arn
}

# We also create the Task Role (which the container itself uses)
resource "aws_iam_role" "fargate_task_role_v2" {
  name = "miso-fargate-task-role-v2"
  # This role is assumed by the task and should have SQS, S3, etc. permissions
  assume_role_policy = jsonencode({
    Version   = "2012-10-17",
    Statement = [
      {
        Effect    = "Allow",
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        },
        Action    = "sts:AssumeRole"
      }
    ]
  })
}
