import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam

class StockPredictor:
    def __init__(self, sequence_length=60):
        self.sequence_length = sequence_length
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.model = None

    def create_sequences(self, data):
        """Create sequences for LSTM input"""
        X = []
        y = []
        data_len = len(data)
        
        for i in range(self.sequence_length, data_len):
            X.append(data[i-self.sequence_length:i])
            y.append(data[i])
            
        return np.array(X), np.array(y)

    def build_model(self, input_shape):
        """Build LSTM model architecture"""
        model = Sequential([
            LSTM(units=50, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(units=50, return_sequences=True),
            Dropout(0.2),
            LSTM(units=50),
            Dropout(0.2),
            Dense(units=1)
        ])
        
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mean_squared_error')
        return model

    def prepare_data(self, df):
        """Prepare data for LSTM model"""
        # Extract relevant features
        features = ['Close', 'Volume', 'MA20', 'MA50', 'Volatility']
        data = df[features].values
        
        # Scale the features
        scaled_data = self.scaler.fit_transform(data)
        
        # Create sequences
        X, y = self.create_sequences(scaled_data)
        
        # Split into train and test sets
        train_size = int(len(X) * 0.8)
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]
        
        return X_train, X_test, y_train, y_test

    def train(self, df, epochs=50, batch_size=32):
        """Train the LSTM model"""
        # Prepare data
        X_train, X_test, y_train, y_test = self.prepare_data(df)
        
        # Build model
        self.model = self.build_model(input_shape=(X_train.shape[1], X_train.shape[2]))
        
        # Train model
        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=(X_test, y_test),
            verbose=1
        )
        
        return history

    def predict_future(self, df, days=30):
        """Predict future stock prices"""
        if self.model is None:
            raise ValueError("Model needs to be trained first")
        
        # Prepare the last sequence from our data
        features = ['Close', 'Volume', 'MA20', 'MA50', 'Volatility']
        last_sequence = df[features].tail(self.sequence_length).values
        last_sequence = self.scaler.transform(last_sequence)
        
        # Make predictions
        future_predictions = []
        current_sequence = last_sequence.copy()
        
        for _ in range(days):
            # Reshape for LSTM input
            current_input = current_sequence.reshape(1, self.sequence_length, len(features))
            
            # Get prediction
            predicted_value = self.model.predict(current_input, verbose=0)
            future_predictions.append(predicted_value[0])
            
            # Update sequence for next prediction
            current_sequence = np.roll(current_sequence, -1, axis=0)
            current_sequence[-1] = predicted_value
            
        # Inverse transform predictions
        future_predictions = np.array(future_predictions)
        padding = np.zeros((len(future_predictions), len(features)))
        padding[:, 0] = future_predictions[:, 0]  # Only care about Close price predictions
        future_predictions = self.scaler.inverse_transform(padding)[:, 0]
        
        # Create future dates
        last_date = pd.to_datetime(df.index[-1])
        future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=days)
        
        return pd.Series(future_predictions, index=future_dates)