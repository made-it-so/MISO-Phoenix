import os
import time
import random
import logging
from flask import Flask, jsonify
from pybreaker import CircuitBreaker, CircuitBreakerError

# --- Basic Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- Circuit Breaker Definition ---
# This breaker will "open" if 5 failures occur within a 60-second window.
# It will then stay open for 30 seconds before entering the "half-open" state
# to test if the dependency is healthy again.
external_service_breaker = CircuitBreaker(fail_max=5, reset_timeout=30)

# --- Mock External Service Call ---
# This function simulates a call to a dependency that might be unreliable.
@external_service_breaker
def call_dependent_service(task_data):
    """
    A function protected by the circuit breaker.
    It simulates a network call that has a 40% chance of failing.
    """
    logger.info(f"Attempting to call dependent service with data: {task_data}")
    if random.random() < 0.4:
        logger.error("Dependent service call failed.")
        # In a real app, this could be requests.exceptions.RequestException, etc.
        raise ConnectionError("Failed to connect to the dependent service")
    
    logger.info("Dependent service call was successful.")
    return {"status": "success", "message": "Data processed by dependent service"}


# --- API Endpoints ---
@app.route('/health', methods=['GET'])
def health_check():
    """Provides a simple health check endpoint."""
    return jsonify({"status": "healthy", "service": "miso-worker"}), 200

@app.route('/process/<task_id>', methods=['POST'])
def process_task(task_id):
    """
    The main endpoint for processing tasks. It relies on the external service.
    """
    logger.info(f"Received request to process task_id: {task_id}")
    try:
        # Call the function that is protected by the circuit breaker
        result = call_dependent_service({"task_id": task_id})
        return jsonify(result), 200
    except CircuitBreakerError:
        logger.warning(
            f"CircuitBreakerError: The circuit is open. "
            f"Call to dependent service was blocked for task_id: {task_id}"
        )
        return jsonify({
            "error": "Service Temporarily Unavailable",
            "message": "The service is currently experiencing issues. Please try again later."
        }), 503  # 503 Service Unavailable is the appropriate response
    except Exception as e:
        logger.error(f"An unexpected error occurred while processing task {task_id}: {e}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred."
        }), 500

# --- Application Runner ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting MISO Worker with Circuit Breaker on port {port}")
    app.run(host='0.0.0.0', port=port)
