from flask import Flask, jsonify, request
import os
from functools import wraps
import datetime

# Initialize Flask app
app = Flask(__name__)

# --- Configuration ---
# In a real application, use environment variables for sensitive data like API keys.
# e.g., SECRET_API_KEY = os.environ.get('PREDICTIVE_API_KEY')
# For this demonstration, a hardcoded key is used.
SECRET_API_KEY = "phoenix-key-alpha-7"

# --- Authentication Decorator ---
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for API key in the 'x-api-key' header
        api_key = request.headers.get('x-api-key')
        if api_key and api_key == SECRET_API_KEY:
            return f(*args, **kwargs)
        else:
            return jsonify({
                "error": "Unauthorized",
                "message": "A valid API key must be provided in the 'x-api-key' header."
            }), 401
    return decorated_function

# --- API Endpoints ---

@app.route('/predict', methods=['GET', 'POST'])
@require_api_key
def predict_market_trends():
    """
    Serves market trend predictions.
    This endpoint is secured and requires a valid API key.
    Accepts GET or POST requests. POST data can be used to refine predictions.
    """
    # Default market sector
    market_sector = 'technology'

    # Check for parameters to customize the prediction
    if request.method == 'POST':
        data = request.get_json()
        market_sector = data.get('market_sector', market_sector)
    elif request.method == 'GET':
        market_sector = request.args.get('market_sector', market_sector)

    # In a real-world scenario, this section would involve complex logic:
    # 1. Fetching real-time market data.
    # 2. Preprocessing the data.
    # 3. Loading a trained machine learning model.
    # 4. Running inference to generate a prediction.
    # For this example, we return static, dummy data.

    dummy_prediction = {
        "requested_sector": market_sector,
        "prediction": {
            "trend": "cautiously_optimistic",
            "confidence_score": 0.82,
            "timeframe": "next_90_days",
            "summary": f"The {market_sector} sector shows strong fundamentals but is sensitive to macroeconomic shifts.",
            "key_indicators": ["Interest Rates", "Supply Chain Health", "Consumer Confidence"]
        },
        "model_version": "pa_v1.3.0-beta",
        "generated_at_utc": datetime.datetime.utcnow().isoformat()
    }

    return jsonify(dummy_prediction)

@app.route('/health', methods=['GET'])
def health_check():
    """
    A simple health check endpoint to confirm the service is running.
    This endpoint is not authenticated.
    """
    return jsonify({"status": "healthy", "service": "PredictiveAnalyticsAPI"}), 200

# --- Main execution block ---
if __name__ == '__main__':
    # Run the app on all available network interfaces.
    # Port 5001 is used to avoid potential conflicts with other services.
    # 'debug=False' is recommended for production environments.
    app.run(host='0.0.0.0', port=5001, debug=False)
