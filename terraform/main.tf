terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Default Provider (us-east-1)
provider "aws" {
  region = "us-east-1"
}

# Secondary Provider (us-west-2)
provider "aws" {
  alias  = "us_west_2"
  region = "us-west-2"
}
