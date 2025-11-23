# --- MISO V7: Dynamic Subnet Lookup ---
# Automatically finds subnets for vpc-0839683a65fa0c5dc
data "aws_vpc" "miso_vpc" {
  id = "vpc-0839683a65fa0c5dc"
}

data "aws_subnets" "miso_subnets" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.miso_vpc.id]
  }
}

# --- MISO V7: Elasticache (Redis) Layer ---
resource "aws_elasticache_subnet_group" "miso_cache_sng" {
  name       = "miso-cache-sng"
  subnet_ids = data.aws_subnets.miso_subnets.ids
}

resource "aws_elasticache_cluster" "miso_msd_cache" {
  cluster_id           = "miso-msd-cache"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  engine_version       = "7.0"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.miso_cache_sng.name
  security_group_ids   = ["sg-0f711e77eb87a4d85"] # Worker/API SG
  tags = {
    Name = "MISO-MSD-Cache"
  }
}

# --- MISO V7: Cross-Cloud Secrets ---
resource "aws_secretsmanager_secret" "gcp_secret" {
  name = "miso/gcp_arbitrage_key"
  description = "GCP Key for Global Arbitrage Engine"
}

resource "aws_secretsmanager_secret" "azure_secret" {
  name = "miso/azure_arbitrage_key"
  description = "Azure Key for Global Arbitrage Engine"
}

resource "aws_secretsmanager_secret_version" "gcp_secret_version" {
  secret_id     = aws_secretsmanager_secret.gcp_secret.id
  secret_string = "{\"gcp_api_key\": \"LITERAL_FAKE_GCP_KEY_FOR_IAC_DEPLOY\"}"
}

resource "aws_secretsmanager_secret_version" "azure_secret_version" {
  secret_id     = aws_secretsmanager_secret.azure_secret.id
  secret_string = "{\"azure_api_key\": \"LITERAL_FAKE_AZURE_KEY_FOR_IAC_DEPLOY\"}"
}
