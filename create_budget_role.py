import boto3
import json

ROLE_NAME = "MISO-Budget-Killer"
POLICY_ARN = "arn:aws:iam::aws:policy/AWSBudgetsActions_RolePolicyForResourceAdministrationWithSSM"

def create_role():
    iam = boto3.client('iam', region_name="us-east-1")
    
    # 1. Define Trust Policy (Allow Budgets Service)
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "budgets.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    print(f"🛡️ Creating IAM Role: {ROLE_NAME}...")
    
    try:
        # Create Role
        response = iam.create_role(
            RoleName=ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Allows AWS Budgets to stop instances when cost exceeds threshold"
        )
        print("✅ Role Created.")
        
        # Attach Managed Policy (The Permission to Kill)
        iam.attach_role_policy(
            RoleName=ROLE_NAME,
            PolicyArn=POLICY_ARN
        )
        print(f"✅ Attached Kill-Switch Policy: {POLICY_ARN}")
        print(f"📌 Role ARN: {response['Role']['Arn']}")
        print("\n👉 ACTION REQUIRED: Go to AWS Console > Budgets > Edit.")
        print(f"   Select '{ROLE_NAME}' in the 'Budget actions' section.")

    except iam.exceptions.EntityAlreadyExistsException:
        print("⚠️ Role already exists. Fetching ARN...")
        role = iam.get_role(RoleName=ROLE_NAME)
        print(f"📌 Role ARN: {role['Role']['Arn']}")
    except Exception as e:
        print(f"❌ FAILED: {e}")

if __name__ == "__main__":
    create_role()
