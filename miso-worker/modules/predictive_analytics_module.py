# modules/predictive_analytics_module.py

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
import joblib
import os
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PredictiveAnalyticsModule:
    """
    A module to forecast future resource usage for enterprise clients
    using historical time-series data.
    """

    def __init__(self, model_path='model_store/resource_usage_model.pkl'):
        """
        Initializes the PredictiveAnalyticsModule.

        Args:
            model_path (str): The path to save/load the trained model.
        """
        self.model_path = model_path
        self.model = None
        self._ensure_model_dir_exists()

    def _ensure_model_dir_exists(self):
        """Ensures the directory for storing the model exists."""
        model_dir = os.path.dirname(self.model_path)
        if model_dir and not os.path.exists(model_dir):
            try:
                os.makedirs(model_dir)
                logging.info(f"Created model directory: {model_dir}")
            except OSError as e:
                logging.error(f"Failed to create model directory {model_dir}: {e}")


    def _preprocess_data(self, df):
        """
        Preprocesses the input DataFrame by creating time-based features.

        Args:
            df (pd.DataFrame): DataFrame with a 'timestamp' column.

        Returns:
            pd.DataFrame: The preprocessed DataFrame.
        """
        if 'timestamp' not in df.columns:
            raise ValueError("Input DataFrame must contain a 'timestamp' column.")

        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['day_of_month'] = df['timestamp'].dt.day
        df['month'] = df['timestamp'].dt.month
        df['year'] = df['timestamp'].dt.year
        # Create a continuous time feature to capture long-term trends
        df['time_index'] = (df['timestamp'] - df['timestamp'].min()).dt.total_seconds() / 3600.0

        return df

    def train_model(self, historical_data, target_column='cpu_usage'):
        """
        Trains a linear regression model on historical resource usage data.

        Args:
            historical_data (pd.DataFrame): A DataFrame containing historical data.
                                            Must include 'timestamp' and the target_column.
            target_column (str): The name of the column to predict.

        Returns:
            float: The Mean Squared Error of the model on the test set.
        """
        logging.info(f"Starting model training for target: {target_column}")

        if not isinstance(historical_data, pd.DataFrame):
            raise TypeError("historical_data must be a pandas DataFrame.")

        if target_column not in historical_data.columns:
            raise ValueError(f"Target column '{target_column}' not found in the data.")

        processed_df = self._preprocess_data(historical_data.copy())

        # Define features and target
        features = ['time_index', 'hour', 'day_of_week', 'day_of_month', 'month', 'year']
        X = processed_df[features]
        y = processed_df[target_column]

        # Split data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)

        # Initialize and train the model
        self.model = LinearRegression()
        self.model.fit(X_train, y_train)
        logging.info("Model training completed.")

        # Evaluate the model
        predictions = self.model.predict(X_test)
        mse = mean_squared_error(y_test, predictions)
        logging.info(f"Model evaluation - Mean Squared Error: {mse:.4f}")

        # Save the trained model
        self.save_model()
        return mse

    def predict_future_usage(self, last_known_timestamp, future_periods=24, freq='H'):
        """
        Forecasts resource usage for a specified number of future periods.

        Args:
            last_known_timestamp (datetime): The last timestamp from the historical data.
            future_periods (int): The number of future periods to forecast.
            freq (str): The frequency of the forecast (e.g., 'H' for hourly, 'D' for daily).

        Returns:
            pd.DataFrame: A DataFrame with future timestamps and their predicted usage.
        """
        if self.model is None:
            self.load_model()
            if self.model is None:
                raise RuntimeError("Model has not been trained or loaded. Please train a model first.")

        logging.info(f"Generating forecast for the next {future_periods} periods with frequency '{freq}'.")

        # Create future timestamps
        future_timestamps = pd.to_datetime(pd.date_range(start=last_known_timestamp, periods=future_periods + 1, freq=freq)[1:])

        future_df = pd.DataFrame({'timestamp': future_timestamps})
        processed_future_df = self._preprocess_data(future_df)

        features = ['time_index', 'hour', 'day_of_week', 'day_of_month', 'month', 'year']
        X_future = processed_future_df[features]

        # Make predictions
        future_predictions = self.model.predict(X_future)

        result_df = pd.DataFrame({
            'timestamp': future_timestamps,
            'predicted_usage': future_predictions
        })

        return result_df

    def save_model(self):
        """Saves the trained model to the specified path."""
        if self.model:
            joblib.dump(self.model, self.model_path)
            logging.info(f"Model saved successfully to {self.model_path}")
        else:
            logging.warning("No model to save. Please train a model first.")

    def load_model(self):
        """Loads a pre-trained model from the specified path."""
        try:
            self.model = joblib.load(self.model_path)
            logging.info(f"Model loaded successfully from {self.model_path}")
        except FileNotFoundError:
            logging.error(f"Model file not found at {self.model_path}. Please train a model first.")
            self.model = None
        except Exception as e:
            logging.error(f"An error occurred while loading the model: {e}")
            self.model = None

def generate_sample_data(periods=720, freq='H'):
    """Generates sample time-series data for demonstration."""
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=periods-1)
    timestamps = pd.date_range(start=start_time, end=end_time, freq=freq)
    
    # Create cyclical patterns (daily, weekly) and a slight upward trend
    time_index = np.arange(len(timestamps))
    daily_cycle = 15 * np.sin(2 * np.pi * timestamps.hour / 24)
    weekly_cycle = 10 * np.sin(2 * np.pi * timestamps.dayofweek / 7)
    trend = 0.01 * time_index
    noise = np.random.normal(0, 5, len(timestamps))
    
    # Base usage + patterns + trend + noise
    cpu_usage = 40 + daily_cycle + weekly_cycle + trend + noise
    cpu_usage = np.clip(cpu_usage, 5, 100) # Ensure usage is within [5, 100]

    data = pd.DataFrame({
        'timestamp': timestamps,
        'cpu_usage': cpu_usage
    })
    return data

if __name__ == '__main__':
    # --- DEMONSTRATION ---
    
    # 1. Initialize the module
    predictor = PredictiveAnalyticsModule(model_path='model_store/demo_cpu_model.pkl')

    # 2. Generate sample historical data
    logging.info("Generating sample historical data for demonstration...")
    historical_data = generate_sample_data(periods=30 * 24) # 30 days of hourly data
    last_ts = historical_data['timestamp'].max()

    # 3. Train the model
    # In a real application, you would load data from a database or a CSV file.
    predictor.train_model(historical_data, target_column='cpu_usage')

    # 4. Forecast future usage
    try:
        logging.info("\nForecasting future CPU usage for the next 24 hours...")
        forecast = predictor.predict_future_usage(last_known_timestamp=last_ts, future_periods=24, freq='H')
        print("--- Future Usage Forecast ---")
        print(forecast.to_string())
        print("---------------------------\n")

    except Exception as e:
        print(f"An error occurred during prediction: {e}")

    # 5. Demonstrate loading a model and predicting again
    logging.info("Demonstrating loading the saved model and re-predicting...")
    new_predictor = PredictiveAnalyticsModule(model_path='model_store/demo_cpu_model.pkl')
    try:
        new_forecast = new_predictor.predict_future_usage(last_known_timestamp=last_ts, future_periods=5, freq='H')
        print("--- Re-prediction Result (first 5 hours) ---")
        print(new_forecast.to_string())
        print("------------------------------------------")
    except Exception as e:
        print(f"An error occurred during re-prediction: {e}")

