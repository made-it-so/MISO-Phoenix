# Look up our existing VPC
data "aws_vpc" "main" {
  id = "vpc-0839683a65fa0c5dc"
}

# Look up the private subnets for Fargate
data "aws_subnets" "private" {
  filter {
    name   = "subnet-id"
    values = ["subnet-029dd1e5b2544816d", "subnet-0a9fa0468b44e7eb4"]
  }
}

# Look up the worker security group
data "aws_security_group" "worker_sg" {
  id = "sg-0f711e77eb87a4d85"
}

# Look up the existing ECS Cluster
data "aws_ecs_cluster" "main" {
  cluster_name = "MISO-Cluster-Elastic"
}
