# MISO V19: Predictive Analytics Agent
# This agent ingests sales and public market data to rank new markets.

import pandas as pd
import numpy as np
import requests
import io
import time
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error

# --- Mock API ---
# In a real scenario, this would be a live API endpoint.
# We'll simulate its behavior for this example.
def mock_api_request(market_name):
    """Simulates a request to a public market data API."""
    print(f"[API] Fetching mock data for {market_name}...")
    # Generate synthetic data based on market name for reproducibility
    hash_val = sum(ord(c) for c in market_name)
    gdp_growth = 1.5 + (hash_val % 20) / 10.0  # Range 1.5 to 3.4
    population = 500000 + (hash_val % 1500000)
    consumer_index = 60 + (hash_val % 40)
    time.sleep(0.1) # Simulate network latency
    return {
        "market": market_name,
        "gdp_growth_percent": gdp_growth,
        "population": population,
        "consumer_confidence_index": consumer_index
    }

class PredictiveAnalyticsAgent:
    """
    An agent to ingest sales data, enrich it with public market data,
    and use a regression model to score and rank potential new markets.
    """

    def __init__(self, api_endpoint="https://api.example.com/marketdata"):
        self.model = LinearRegression()
        self.scaler = StandardScaler()
        self.api_endpoint = api_endpoint
        self.historical_features = None
        print("MISO V19: Predictive Analytics Agent Initialized.")

    def ingest_sales_data(self):
        """
        Ingests historical sales data. In a real-world application,
        this would connect to a database or read from a data warehouse.
        """
        print("[Ingest] Loading historical sales data...")
        # Sample historical data: Market, economic factors, and resulting sales growth
        csv_data = """market,gdp_growth_percent,population,consumer_confidence_index,sales_growth_actual
Metro_A,2.5,1200000,85,5.2
Metro_B,1.8,800000,72,3.1
Metro_C,3.1,2500000,95,6.5
Metro_D,2.2,500000,88,4.0
Metro_E,1.5,300000,65,2.1
Metro_F,2.8,1800000,91,5.9
Metro_G,3.5,3000000,98,7.2
"""
        try:
            data = pd.read_csv(io.StringIO(csv_data))
            print("[Ingest] Historical sales data loaded successfully.")
            return data
        except Exception as e:
            print(f"[Error] Failed to ingest sales data: {e}")
            return pd.DataFrame()

    def fetch_market_data(self, markets):
        """
        Fetches public market data for a list of potential new markets.
        """
        print(f"[API] Fetching public data for {len(markets)} new markets...")
        market_data = []
        for market in markets:
            try:
                # In a real scenario, you'd use requests:
                # response = requests.get(f"{self.api_endpoint}?market={market}")
                # response.raise_for_status()
                # data = response.json()
                
                # Using the mock API for this example
                data = mock_api_request(market)
                market_data.append(data)
            except requests.exceptions.RequestException as e:
                print(f"[Error] API call failed for market {market}: {e}")
        return pd.DataFrame(market_data)

    def train_model(self, historical_data):
        """
        Trains a regression model on historical data to predict sales growth.
        """
        print("[Train] Starting model training...")
        if historical_data.empty:
            print("[Error] No historical data to train on. Aborting.")
            return

        features = ['gdp_growth_percent', 'population', 'consumer_confidence_index']
        target = 'sales_growth_actual'

        X = historical_data[features]
        y = historical_data[target]
        
        # Scale features
        self.historical_features = features
        X_scaled = self.scaler.fit_transform(X)

        # Train the model
        self.model.fit(X_scaled, y)
        print("[Train] Model training complete.")

        # Optional: Evaluate model
        predictions = self.model.predict(X_scaled)
        mse = mean_squared_error(y, predictions)
        print(f"[Train] Model MSE on training data: {mse:.2f}")

    def score_and_rank_markets(self, new_market_data):
        """
        Uses the trained model to score potential new markets and ranks them.
        """
        print("[Score] Scoring and ranking potential new markets...")
        if new_market_data.empty or self.historical_features is None:
            print("[Error] No new market data or model not trained. Aborting.")
            return pd.DataFrame()

        # Ensure columns are in the same order as during training
        X_new = new_market_data[self.historical_features]

        # Scale the new data using the same scaler from training
        X_new_scaled = self.scaler.transform(X_new)

        # Predict growth potential
        predicted_growth = self.model.predict(X_new_scaled)
        new_market_data['predicted_growth_score'] = predicted_growth

        # Rank markets by the predicted score in descending order
        ranked_markets = new_market_data.sort_values(by='predicted_growth_score', ascending=False)
        print("[Score] Ranking complete.")
        return ranked_markets

    def run(self):
        """
        Main execution pipeline for the agent.
        """
        print("\n--- Starting Predictive Analytics Pipeline ---")
        
        # 1. Ingest historical data
        historical_data = self.ingest_sales_data()
        if historical_data.empty:
            return # Stop if data ingestion fails
        
        # 2. Train model on historical data
        self.train_model(historical_data)
        
        # 3. Define potential new markets to evaluate
        potential_markets = ['Urban_X', 'Suburban_Y', 'Coastal_Z', 'Mountain_W', 'Rural_V']
        
        # 4. Fetch public data for these new markets
        new_market_data = self.fetch_market_data(potential_markets)
        if new_market_data.empty:
            return # Stop if API calls fail
            
        # 5. Score and rank the new markets
        ranked_markets = self.score_and_rank_markets(new_market_data)
        
        print("\n--- Predictive Analytics Results ---")
        if not ranked_markets.empty:
            print("Top Potential New Markets Ranked by Growth Potential:")
            print(ranked_markets[['market', 'predicted_growth_score']].to_string(index=False))
        else:
            print("Could not generate market rankings.")
            
        print("\n--- Pipeline Finished ---")


if __name__ == "__main__":
    # Check for necessary libraries and provide guidance if they are missing.
    try:
        import pandas as pd
        import sklearn
        import requests
    except ImportError:
        print("Dependencies not found. Please install them by running:")
        print("pip install pandas scikit-learn requests")
        exit(1)
        
    agent = PredictiveAnalyticsAgent()
    agent.run()
