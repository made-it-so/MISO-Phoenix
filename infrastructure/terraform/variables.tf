variable "aws_region" { default = "us-east-1" }
variable "vpc_id" {}
variable "subnet_ids" { type = list(string) }
variable "db_root_password" {}
variable "worker_ami_id" {}
variable "k8s_token" { default = "temporary-token-placeholder" }
variable "master_ip" { default = "10.0.1.50" }
