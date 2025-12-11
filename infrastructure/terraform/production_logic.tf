# --- NETWORK SECURITY ---
resource "aws_security_group" "miso_db_sg" {
  name        = "miso-phoenix-db-sg"
  description = "Allow inbound traffic from K8s Compute"
  vpc_id      = var.vpc_id

  ingress {
    description = "Postgres Internal"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"] 
  }
}

# --- DB ---
resource "aws_db_instance" "miso_ledger" {
  identifier        = "miso-phoenix-ledger-prod"
  engine            = "postgres"
  engine_version    = "15" 
  instance_class    = "db.t3.micro" 
  allocated_storage = 20           
  db_name           = "miso_ledger"
  username          = "miso_admin"
  password          = var.db_root_password 
  skip_final_snapshot = true
  publicly_accessible = false
  vpc_security_group_ids = [aws_security_group.miso_db_sg.id]
}

# --- COMPUTE ---
resource "aws_launch_template" "miso_worker" {
  name_prefix   = "miso-muscle-"
  image_id      = var.worker_ami_id 
  instance_type = "c5.2xlarge"      

  instance_market_options {
    market_type = "spot"
    spot_options {
      max_price = "0.25" 
    }
  }

  # THE FIX: FORCE PUBLIC IP
  # This gives the instance internet access to download MicroK8s
  network_interfaces {
    associate_public_ip_address = true
    security_groups             = [] # Uses default VPC SG
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "MISO-Muscle-Spot"
      role = "muscle"
      tier = "spot"
    }
  }

  user_data = base64encode(<<-USERDATA
              #!/bin/bash
              set -e
              echo "🛠 Installing MicroK8s..."
              snap install microk8s --classic --channel=1.32/stable
              echo "⏳ Waiting for socket..."
              microk8s status --wait-ready --timeout 300
              echo "🔗 Joining Cluster..."
              for i in {1..5}; do
                microk8s join ${var.master_ip}:25000/${var.k8s_token} --worker && break
                echo "⚠️ Join failed. Retrying in 10s..."
                sleep 10
              done
              /snap/bin/microk8s.kubectl label node $(hostname) role=muscle tier=spot --overwrite
              USERDATA
  )
}

resource "aws_autoscaling_group" "miso_muscles" {
  name                = "miso-worker-pool-live"
  vpc_zone_identifier = var.subnet_ids
  min_size            = 0
  max_size            = 10
  desired_capacity    = 1

  launch_template {
    id      = aws_launch_template.miso_worker.id
    version = "$Latest"
  }
  
  lifecycle {
    create_before_destroy = true
  }
}
