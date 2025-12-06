# broker.ps1
# Usage: .\broker.ps1 -Prompt "Your custom prompt here"

param (
    [string]$Prompt = "Explain 'Data Gravity' like a pirate. Keep it under 50 words."
)

# 1. Detect Queue URL
Write-Host "--- Broker: Locating Order Book (SQS Queue) ---"
$QueueUrl = aws sqs get-queue-url --queue-name miso_job_queue --query QueueUrl --output text

if (-not $QueueUrl) {
    Write-Error "Could not find 'miso_job_queue'. Is your AWS CLI configured?"
    exit 1
}

# 2. Construct the 'Persona' Contract
$Persona = @{
    task_id = [Guid]::NewGuid().ToString()
    task_type = "generate_intelligence"
    payload = @{
        prompt = $Prompt
    }
    routing_instructions = @{
        model_tier = "flash"
        max_cost = 0.001
    }
}

# 3. Write to Temp File (Bypasses PowerShell escaping issues)
$Persona | ConvertTo-Json -Depth 5 | Out-File -FilePath "temp_task.json" -Encoding ASCII

# 4. Dispatch the Order using file:// protocol
Write-Host "--- Broker: Routing Persona to SQS ---"
Write-Host "Target: $QueueUrl"

try {
    aws sqs send-message --queue-url $QueueUrl --message-body file://temp_task.json
    Write-Host "--- Task Dispatched. Monitor CloudWatch for 'TASK_COMPLETE'. ---"
}
finally {
    # Cleanup
    if (Test-Path "temp_task.json") { Remove-Item "temp_task.json" }
}
