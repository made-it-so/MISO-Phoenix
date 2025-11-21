# Log Group for the default US-EAST-1 region (Original Reference Name)
resource "aws_cloudwatch_log_group" "worker_logs" {
  name = "/ecs/miso-worker-task"
}

# Log Group for the US-WEST-2 region (New deployment target)
resource "aws_cloudwatch_log_group" "worker_logs_west" {
  provider = aws.us_west_2
  name     = "/ecs/miso-worker-task-us-west-2"
}
