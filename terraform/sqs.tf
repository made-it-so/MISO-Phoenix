# 1. Primary SQS Queue (US-EAST-1 Default Provider)
# This resource MUST exist for the existing ECS configuration to compile.
resource "aws_sqs_queue" "job_queue" {
  name                       = "miso_job_queue"
  fifo_queue                 = false
  visibility_timeout_seconds = 300
}

# 2. Secondary SQS Queue (US-WEST-2 Alias)
resource "aws_sqs_queue" "job_queue_west" {
  provider                   = aws.us_west_2
  name                       = "miso_job_queue_west"
  fifo_queue                 = false
  visibility_timeout_seconds = 300
}
