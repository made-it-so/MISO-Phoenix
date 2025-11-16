resource "aws_sqs_queue" "job_queue" {
  name                       = "miso_job_queue"
  fifo_queue                 = false
  visibility_timeout_seconds = 300
}
