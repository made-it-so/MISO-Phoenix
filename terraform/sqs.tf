# 1. DLQ for Primary (US-EAST-1)
resource "aws_sqs_queue" "job_queue_dlq" {
  name = "miso_job_queue_dlq"
}

# 2. Primary SQS Queue (US-EAST-1 Default Provider)
resource "aws_sqs_queue" "job_queue" {
  name                       = "miso_job_queue"
  fifo_queue                 = false
  visibility_timeout_seconds = 300
  
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.job_queue_dlq.arn
    maxReceiveCount     = 3 # Task is moved to DLQ after 3 failed attempts
  })
}

# 3. DLQ for Secondary (US-WEST-2)
resource "aws_sqs_queue" "job_queue_west_dlq" {
  provider = aws.us_west_2
  name     = "miso_job_queue_west_dlq"
}

# 4. Secondary SQS Queue (US-WEST-2 Alias)
resource "aws_sqs_queue" "job_queue_west" {
  provider                   = aws.us_west_2
  name                       = "miso_job_queue_west"
  fifo_queue                 = false
  visibility_timeout_seconds = 300
  
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.job_queue_west_dlq.arn
    maxReceiveCount     = 3 # Task is moved to DLQ after 3 failed attempts
  })
}
