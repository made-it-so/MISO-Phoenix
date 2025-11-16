resource "aws_cloudwatch_log_group" "worker_logs" {
  name = "/ecs/miso-worker-task"
}
