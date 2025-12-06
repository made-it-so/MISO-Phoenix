# 1. Lambda Execution Role
resource "aws_iam_role" "lambda_exec_role" {
  name = "miso-broker-lambda-exec-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = { Service = "lambda.amazonaws.com" },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# 2. Lambda Policy (Allows Logs, Secrets, SQS Write, DynamoDB R/W)
resource "aws_iam_policy" "lambda_broker_policy" {
  name = "MISO-Broker-Lambda-Policy"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow",
        Action = [
          "sqs:SendMessage",
          "sqs:GetQueueUrl"
        ],
        Resource = "*" # Will be restricted later
      },
      {
        Effect = "Allow",
        Action = ["dynamodb:PutItem", "dynamodb:Query"],
        Resource = "*" # Will be restricted later
      },
      {
        Effect = "Allow",
        Action = "secretsmanager:GetSecretValue",
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_lambda_policy" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.lambda_broker_policy.arn
}

# 3. Serverless Lambda Function (Placeholder for the API Broker logic)
resource "aws_lambda_function" "persona_broker" {
  function_name    = "miso-persona-broker"
  runtime          = "python3.11"
  handler          = "main.lambda_handler"
  role             = aws_iam_role.lambda_exec_role.arn
  timeout          = 30 # Time for LLM generation
  memory_size      = 256
  
  # Note: The deployment package must be updated with the compiled API logic.
  # For now, we use a small zip placeholder.
  filename = "broker_placeholder.zip" 
  source_code_hash = filebase64sha256("broker_placeholder.zip")
}

# 4. API Gateway (The new public front door)
resource "aws_apigatewayv2_api" "broker_api" {
  name          = "MISO-Broker-API"
  protocol_type = "HTTP"
  target        = aws_lambda_function.persona_broker.arn
}
