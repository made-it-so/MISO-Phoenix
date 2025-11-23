resource "aws_dynamodb_table" "replay_buffer" {
  name           = "miso_replay_buffer"
  billing_mode   = "PAY_PER_REQUEST" # True serverless (Cost =  if idle)
  hash_key       = "task_id"
  
  attribute {
    name = "task_id"
    type = "S"
  }

  # GSI for querying by Intent (e.g., "Find all successful 'refactor' plans")
  attribute {
    name = "intent"
    type = "S"
  }

  global_secondary_index {
    name               = "IntentIndex"
    hash_key           = "intent"
    projection_type    = "ALL"
  }

  tags = {
    Name = "MISO Replay Buffer"
    Role = "Memory"
  }
}
