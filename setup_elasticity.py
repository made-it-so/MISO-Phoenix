import boto3
import time

REGION = "us-east-1"
CLUSTER = "MISO-Cluster-Elastic"
SERVICE = "miso-worker-service-iac"
QUEUE = "miso_job_queue"

app = boto3.client('application-autoscaling', region_name=REGION)
cw = boto3.client('cloudwatch', region_name=REGION)

def setup_scaling():
    print("⚖️  Configuring Auto-Wake/Auto-Sleep Rules...")

    # 1. Register Scalable Target (0 to 10 workers)
    app.register_scalable_target(
        ServiceNamespace='ecs',
        ResourceId=f'service/{CLUSTER}/{SERVICE}',
        ScalableDimension='ecs:service:DesiredCount',
        MinCapacity=0,
        MaxCapacity=10
    )

    # 2. Scale UP Policy (Add 1 worker)
    up_policy = app.put_scaling_policy(
        PolicyName='MISO-ScaleUp',
        ServiceNamespace='ecs',
        ResourceId=f'service/{CLUSTER}/{SERVICE}',
        ScalableDimension='ecs:service:DesiredCount',
        PolicyType='StepScaling',
        StepScalingPolicyConfiguration={
            'AdjustmentType': 'ChangeInCapacity',
            'StepAdjustments': [{'MetricIntervalLowerBound': 0, 'ScalingAdjustment': 1}],
            'Cooldown': 60,
            'MetricAggregationType': 'Maximum'
        }
    )
    
    # 3. Scale DOWN Policy (Remove 1 worker)
    down_policy = app.put_scaling_policy(
        PolicyName='MISO-ScaleDown',
        ServiceNamespace='ecs',
        ResourceId=f'service/{CLUSTER}/{SERVICE}',
        ScalableDimension='ecs:service:DesiredCount',
        PolicyType='StepScaling',
        StepScalingPolicyConfiguration={
            'AdjustmentType': 'ChangeInCapacity',
            'StepAdjustments': [{'MetricIntervalUpperBound': 0, 'ScalingAdjustment': -1}],
            'Cooldown': 300, # Wait 5 mins before killing
            'MetricAggregationType': 'Maximum'
        }
    )

    # 4. CloudWatch Alarm: Wake Up (Queue > 0)
    cw.put_metric_alarm(
        AlarmName='MISO-WakeUp',
        MetricName='ApproximateNumberOfMessagesVisible',
        Namespace='AWS/SQS',
        Dimensions=[{'Name': 'QueueName', 'Value': QUEUE}],
        Statistic='Sum',
        Period=60,
        EvaluationPeriods=1,
        Threshold=0,
        ComparisonOperator='GreaterThanThreshold',
        AlarmActions=[up_policy['PolicyARN']]
    )

    # 5. CloudWatch Alarm: Sleep (Queue == 0)
    cw.put_metric_alarm(
        AlarmName='MISO-Sleep',
        MetricName='ApproximateNumberOfMessagesVisible',
        Namespace='AWS/SQS',
        Dimensions=[{'Name': 'QueueName', 'Value': QUEUE}],
        Statistic='Sum',
        Period=300, # 5 minutes empty
        EvaluationPeriods=1,
        Threshold=0,
        ComparisonOperator='LessThanOrEqualToThreshold',
        AlarmActions=[down_policy['PolicyARN']]
    )
    
    print("✅ Elasticity Rules Applied.")
    print("   - MISO will now wake up automatically when jobs arrive.")
    print("   - MISO will sleep automatically after 5 mins of idleness.")

if __name__ == "__main__":
    setup_scaling()
