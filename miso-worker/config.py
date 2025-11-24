# MISO Worker Configuration
# Service V19.0

# General Settings
LOG_LEVEL = "INFO"
HEARTBEAT_INTERVAL = 5 # Reduced for faster response
MAX_CONCURRENT_TASKS = 8 # Increased capacity

# Memory and Feedback Systems
# PRIORITY ALPHA DIRECTIVE: Fast-frequency feedback loop activated.
FAST_FREQUENCY_FEEDBACK_ENABLED = True
CONTINUUM_ENDPOINT = "http://localhost:8001/update"

# Resource Management
CPU_THROTTLE_PERCENT = 90
MEMORY_CEILING_MB = 4096
