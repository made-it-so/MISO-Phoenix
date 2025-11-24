import os
import json
import time
import hmac
import threading
from datetime import datetime, timezone
from flask import Flask, jsonify, request

# --- Configuration ---
REPORT_FILE = 'market_report.json'
UPDATE_INTERVAL_SECONDS = 3600  # Update report every hour
VALID_API_KEY = os.getenv('VALID_API_KEY', 'phoenix-secret-key-xyz789') # Use environment variable or a default
HOST = '127.0.0.1' # Binds to localhost only for security
PORT = 5001

app = Flask(__name__)

# --- Core Logic: Market Analysis Generation ---
def generate_market_analysis():
    """
    Generates a mock market analysis report and saves it to a JSON file.
    In a real-world scenario, this would involve complex data aggregation and analysis.
    """
    print(f"[{datetime.now()}] Generating new market analysis report...")
    report_data = {
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'report_id': f"mrkt_{int(time.time())}",
        'market_summary': {
            'market': 'Global AI-Powered Automation',
            'market_size_usd': '15.7 Trillion by 2030',
            'cagr': '22.5%',
            'key_players': ['MISO-Phoenix', 'Google AI', 'OpenAI', 'NVIDIA', 'Microsoft Azure'],
        },
        'emerging_trends': [
            'Hyper-automation in enterprise workflows',
            'Generative AI for content creation and data synthesis',
            'Edge AI for real-time processing',
            'AI-driven cybersecurity threats and defenses',
        ],
        'competitor_analysis': {
            'competitor_a': {'strategy': 'Focus on large language models', 'risk': 'High computational cost'},
            'competitor_b': {'strategy': 'Vertical integration with cloud services', 'risk': 'Potential for vendor lock-in'},
        },
        'investment_outlook': 'Strongly positive, with significant venture capital inflow into AI startups.'
    }
    try:
        with open(REPORT_FILE, 'w') as f:
            json.dump(report_data, f, indent=4)
        print(f"[{datetime.now()}] Report successfully saved to {REPORT_FILE}")
    except IOError as e:
        print(f"Error writing report file: {e}")

# --- Background Task: Periodic Report Update ---
def update_report_periodically():
    """
    Continuously calls the report generation function at a set interval.
    Waits for the first interval before the first update.
    """
    while True:
        time.sleep(UPDATE_INTERVAL_SECONDS)
        generate_market_analysis()

# --- API Endpoint Definition ---
@app.route('/api/v1/market_report', methods=['GET'])
def get_market_report():
    """
    Exposes the market analysis report via a monetized API endpoint.
    Access is restricted by an API key provided in the headers.
    """
    # Monetization Step: Check for a valid API key
    api_key = request.headers.get('X-API-KEY')
    # Securely compare keys to prevent timing attacks
    if not api_key or not hmac.compare_digest(api_key, VALID_API_KEY):
        return jsonify({'error': 'Unauthorized. A valid X-API-KEY header is required.'}), 401

    # Serve the report if the key is valid
    try:
        with open(REPORT_FILE, 'r') as f:
            report_data = json.load(f)
        return jsonify(report_data)
    except FileNotFoundError:
        return jsonify({'error': 'Market report not found. Please try again later.'}), 404
    except Exception as e:
        return jsonify({'error': f'An internal error occurred: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """A simple health check endpoint to confirm the server is running."""
    return jsonify({'status': 'ok'}), 200

# --- Main Execution ---
if __name__ == '__main__':
    # 1. Generate the first report immediately on startup to ensure the file exists.
    print("MISO V19 Data Monetization Agent Initializing...")
    generate_market_analysis()

    # 2. Start the background thread for periodic updates.
    # The 'daemon=True' ensures the thread exits when the main program does.
    report_updater_thread = threading.Thread(target=update_report_periodically, daemon=True)
    report_updater_thread.start()
    print(f"Background report updater started. Next update in {UPDATE_INTERVAL_SECONDS} seconds.")

    # 3. Start the Flask web server to serve the API.
    print(f"Starting API server at http://{HOST}:{PORT}")
    print("Endpoint: /api/v1/market_report")
    print(f"Required Header: X-API-KEY: {VALID_API_KEY}")
    app.run(host=HOST, port=PORT)
