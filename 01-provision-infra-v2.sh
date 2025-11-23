#!/bin/bash
set -e

# --- CONFIGURATION ---
VPC_ID="vpc-0839683a65fa0c5dc"
REGION="us-east-1"
PUBLIC_SUBNET_A="subnet-01df846c12e725654"

echo "### MISO PHASE 1: STARTING INFRASTRUCTURE BUILD (v2) ###"

# --- 1. PRIVATE SUBNETS ---
# Using 172.31.50.0/24 and 172.31.51.0/24.
# These are valid ranges within the default 172.31.0.0/16 VPC.
echo "Provisioning Private Subnets..."
PRIVATE_SUBNET_1A=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 172.31.50.0/24 \
    --availability-zone ${REGION}a \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=miso-private-us-east-1a}]' \
    --region $REGION \
    --query 'Subnet.SubnetId' --output text)

PRIVATE_SUBNET_1B=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 172.31.51.0/24 \
    --availability-zone ${REGION}b \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=miso-private-us-east-1b}]' \
    --region $REGION \
    --query 'Subnet.SubnetId' --output text)

echo "Created Private Subnets: $PRIVATE_SUBNET_1A and $PRIVATE_SUBNET_1B"
echo "---"

# --- 2. NAT GATEWAY ---
echo "Provisioning Elastic IP for NAT Gateway..."
EIP_ALLOC_ID=$(aws ec2 allocate-address \
    --domain vpc \
    --tag-specifications 'ResourceType=elastic-ip,Tags=[{Key=Name,Value=miso-nat-eip}]' \
    --region $REGION \
    --query 'AllocationId' --output text)

echo "Provisioning NAT Gateway in $PUBLIC_SUBNET_A..."
NAT_GW_ID=$(aws ec2 create-nat-gateway \
    --subnet-id $PUBLIC_SUBNET_A \
    --allocation-id $EIP_ALLOC_ID \
    --tag-specifications 'ResourceType=natgateway,Tags=[{Key=Name,Value=miso-nat-gw}]' \
    --region $REGION \
    --query 'NatGateway.NatGatewayId' --output text)

echo "Created NAT Gateway: $NAT_GW_ID. Waiting for status 'available'..."
aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT_GW_ID --region $REGION
echo "NAT Gateway is available."
echo "---"

# --- 3. PRIVATE ROUTE TABLE ---
echo "Provisioning Private Route Table..."
PRIVATE_RTB_ID=$(aws ec2 create-route-table \
    --vpc-id $VPC_ID \
    --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=miso-private-rtb}]' \
    --region $REGION \
    --query 'RouteTable.RouteTableId' --output text)

echo "Created Private Route Table: $PRIVATE_RTB_ID"
echo "Adding 0.0.0.0/0 route to NAT Gateway $NAT_GW_ID..."

aws ec2 create-route \
    --route-table-id $PRIVATE_RTB_ID \
    --destination-cidr-block 0.0.0.0/0 \
    --nat-gateway-id $NAT_GW_ID \
    --region $REGION

echo "Associating Route Table with Private Subnets..."
aws ec2 associate-route-table \
    --route-table-id $PRIVATE_RTB_ID \
    --subnet-id $PRIVATE_SUBNET_1A \
    --region $REGION

aws ec2 associate-route-table \
    --route-table-id $PRIVATE_RTB_ID \
    --subnet-id $PRIVATE_SUBNET_1B \
    --region $REGION

echo "Private routing is complete."
echo "---"

# --- 4. SQS QUEUE ---
echo "Creating SQS Queue: miso_job_queue..."
SQS_QUEUE_URL=$(aws sqs create-queue \
    --queue-name miso_job_queue \
    --attributes '{"VisibilityTimeout":"900"}' \
    --tags '{"Project":"MISO"}' \
    --region $REGION \
    --query 'QueueUrl' --output text)

echo "Created SQS Queue. URL: $SQS_QUEUE_URL"
echo "---"
echo "### MISO PHASE 1: INFRASTRUCTURE COMPLETE ###"
echo "NEW PRIVATE SUBNETS: $PRIVATE_SUBNET_1A, $PRIVATE_SUBNET_1B"
echo "NEW SQS URL: $SQS_QUEUE_URL"
