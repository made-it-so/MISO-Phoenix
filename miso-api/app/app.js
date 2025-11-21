const API_ENDPOINT = 'https://miso.stemcultivation.com/task'; 

document.getElementById('dashboardLink').href = 'https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=MISO-Fintech-Telemetry';

async function submitTask() {
    const prompt = document.getElementById('promptInput').value;
    const responseBox = document.getElementById('responseBox');
    
    if (!prompt) {
        responseBox.innerHTML = 'Please enter a task prompt.';
        return;
    }

    responseBox.innerHTML = 'Submitting task to Broker (Layer 1)...';

    const payload = {
        prompt: prompt,
        priority: 'high',
        max_cost: 0.50
    };

    try {
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        });

        const data = await response.json();
        
        if (!response.ok) {
            responseBox.className = 'response-box status-failure';
            responseBox.innerHTML = ERROR (): ;
            return;
        }

        // Display the successful routing decision
        const output = \
STATUS: SUCCESS - Persona Dispatched
SOURCE: \ (Metacognitive Check)
MODEL TIER: \
TARGET REGION: \ (Geo-Compute Arbitrage)
TASK ID: \
\;
        
        responseBox.className = 'response-box status-success';
        responseBox.innerHTML = output;

    } catch (error) {
        // This catch block will execute due to the local firewall (Unable to connect)
        responseBox.className = 'response-box status-failure';
        responseBox.innerHTML = FATAL CLIENT ERROR: Network Blocked or API Down. Check Firewall/ALB.;
    }
}
