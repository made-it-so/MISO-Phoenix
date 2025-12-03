
provider "aws" {
  region = "us-east-1"
}

# The MISO Spot Fleet Request
resource "aws_spot_instance_request" "miso_worker" {
  ami           = "ami-0c7217cdde317cfec" # Ubuntu 22.04 LTS
  instance_type = "t3.medium"
  spot_price    = "0.015" # Max price willing to pay
  wait_for_fulfillment = true
  
  tags = {
    Name = "MISO-V85-Spot-Worker"
  }
}
