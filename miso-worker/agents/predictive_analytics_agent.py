import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, roc_auc_score
import logging
import os
import datetime
import json

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PredictiveAnalyticsAgent:
    """
    Analyzes market and CRM data to identify and score high-potential enterprise leads.
    This agent simulates the process of:
    1. Loading data from a CRM and external market data sources.
    2. Preprocessing and merging the data.
    3. Training a predictive model on historical data (e.g., past successful conversions).
    4. Using the model to score new, unscored leads.
    5. Saving the scored leads for sales team action.
    """
    def __init__(self, crm_path='data/crm_data.csv', market_data_path='data/market_data.csv', output_path='output/scored_leads.csv'):
        self.crm_path = crm_path
        self.market_data_path = market_data_path
        self.output_path = output_path
        self.model = None
        self.preprocessor = None
        
        # Ensure data and output directories exist
        os.makedirs(os.path.dirname(crm_path), exist_ok=True)
        os.makedirs(os.path.dirname(market_data_path), exist_ok=True)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

    def _generate_dummy_data(self):
        """Generates dummy CRM and Market data for demonstration purposes."""
        logger.info("Generating dummy data as source files not found...")
        
        # Dummy CRM Data
        crm_data = {
            'company_id': range(1, 101),
            'company_name': [f'Enterprise_{i}' for i in range(1, 101)],
            'contact_email': [f'contact@enterprise{i}.com' for i in range(1, 101)],
            'last_interaction_days_ago': np.random.randint(1, 365, 100),
            'deal_size': np.random.randint(50000, 500000, 100),
            'converted_deal': np.random.choice([0, 1], 100, p=[0.7, 0.3]) # 30% conversion rate
        }
        pd.DataFrame(crm_data).to_csv(self.crm_path, index=False)

        # Dummy Market Data
        market_data = {
            'company_id': range(1, 101),
            'industry': np.random.choice(['Tech', 'Finance', 'Healthcare', 'Manufacturing', 'Retail'], 100),
            'company_size': np.random.choice(['100-500', '501-2000', '2001-10000', '10000+'], 100),
            'funding_raised_millions': np.random.uniform(10, 500, 100).round(2),
            'region': np.random.choice(['NA', 'EMEA', 'APAC'], 100)
        }
        pd.DataFrame(market_data).to_csv(self.market_data_path, index=False)
        logger.info(f"Dummy data saved to {self.crm_path} and {self.market_data_path}")

    def _load_data(self):
        """Loads CRM and market data from CSV files."""
        try:
            crm_df = pd.read_csv(self.crm_path)
            market_df = pd.read_csv(self.market_data_path)
            logger.info("Successfully loaded CRM and market data.")
            return crm_df, market_df
        except FileNotFoundError:
            self._generate_dummy_data()
            return pd.read_csv(self.crm_path), pd.read_csv(self.market_data_path)

    def _preprocess_and_merge(self, crm_df, market_df):
        """Merges, cleans, and prepares data for model training."""
        logger.info("Preprocessing and merging data...")
        # Merge data on a common key
        df = pd.merge(crm_df, market_df, on='company_id')

        # Simple feature engineering
        df['funding_per_size'] = df['funding_raised_millions'] / df['company_size'].apply(lambda x: int(x.split('-')[0].replace('+', ''))).astype(float)
        
        # Handle potential missing values (if any)
        df.fillna(0, inplace=True)
        
        logger.info("Data preprocessing complete. Final features: %s", df.columns.tolist())
        return df

    def train_model(self, df):
        """Trains a classification model to predict lead conversion."""
        logger.info("Starting model training...")
        
        # Define features (X) and target (y)
        # We assume 'converted_deal' is our historical target
        features = ['last_interaction_days_ago', 'deal_size', 'industry', 'company_size', 'funding_raised_millions', 'region', 'funding_per_size']
        target = 'converted_deal'

        X = df[features]
        y = df[target]

        # Identify categorical and numerical features
        categorical_features = ['industry', 'company_size', 'region']
        numerical_features = ['last_interaction_days_ago', 'deal_size', 'funding_raised_millions', 'funding_per_size']

        # Create a preprocessing pipeline
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', 'passthrough', numerical_features),
                ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
            ])

        # Create the full model pipeline
        self.model = Pipeline(steps=[('preprocessor', preprocessor),
                                     ('classifier', RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced'))])
        
        # Split data for training and validation
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        
        # Train the model
        self.model.fit(X_train, y_train)
        
        # Evaluate the model
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        
        accuracy = accuracy_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_pred_proba)
        
        logger.info(f"Model training complete. Validation Accuracy: {accuracy:.4f}, Validation AUC: {auc:.4f}")

    def score_leads(self, df):
        """Scores all leads in the dataframe using the trained model."""
        logger.info("Scoring leads...")
        if self.model is None:
            logger.error("Model has not been trained. Cannot score leads.")
            raise ValueError("Model is not trained. Please run train_model() first.")
            
        features = ['last_interaction_days_ago', 'deal_size', 'industry', 'company_size', 'funding_raised_millions', 'region', 'funding_per_size']
        leads_to_score = df[features]
        
        # Predict probability of conversion (class 1)
        probabilities = self.model.predict_proba(leads_to_score)[:, 1]
        
        # Assign a score from 0 to 100
        df['lead_score'] = (probabilities * 100).round(2)
        
        logger.info("Lead scoring complete.")
        return df

    def save_scored_leads(self, scored_df):
        """Saves the scored leads to a CSV file, ordered by score."""
        sorted_df = scored_df.sort_values(by='lead_score', ascending=False)
        
        # Select key columns for the final report
        output_columns = ['company_id', 'company_name', 'contact_email', 'industry', 'company_size', 'deal_size', 'lead_score']
        final_df = sorted_df[output_columns]
        
        final_df.to_csv(self.output_path, index=False)
        logger.info(f"High-potential leads saved to {self.output_path}")

    def run(self):
        """
        Executes the full pipeline: load, preprocess, train, score, and save.
        """
        logger.info("Starting Predictive Analytics Agent workflow...")
        
        # 1. Load Data
        crm_df, market_df = self._load_data()
        
        # 2. Preprocess and Merge Data
        full_df = self._preprocess_and_merge(crm_df, market_df)
        
        # 3. Train Model on historical data (where 'converted_deal' is known)
        historical_df = full_df[full_df['converted_deal'].notna()]
        if historical_df.empty:
            logger.error("No historical data with conversion status to train on. Exiting.")
            return
        self.train_model(historical_df)
        
        # 4. Score all leads (can be historical or new)
        scored_df = self.score_leads(full_df)
        
        # 5. Save Results
        self.save_scored_leads(scored_df)
        
        logger.info("Predictive Analytics Agent workflow finished successfully.")

if __name__ == "__main__":
    # Example usage:
    # Initialize the agent with specified data paths.
    # In a real application, these paths might point to a data lake or warehouse.
    agent = PredictiveAnalyticsAgent(
        crm_path='data/crm_enterprise_data.csv',
        market_data_path='data/market_intelligence_data.csv',
        output_path=f'output/scored_enterprise_leads_{datetime.date.today()}.csv'
    )
    
    # Run the agent's full process.
    agent.run()
