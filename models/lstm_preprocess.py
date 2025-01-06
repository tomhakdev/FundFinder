import numpy as np
from sklearn.preprocessing import MinMaxScaler

def preprocess_data(df, sequence_length=60):
    """
    Preprocess stock data for LSTM model.
    :param df: DataFrame containing stock data with features
    :param sequence_length: Length of the sequences for LSTM
    :return: Scaled data, scaler, sequences (X), and labels (y)
    """
    features = ['Close', 'Volume', 'MA20', 'MA50', 'Volatility', 'RSI']
    data = df[features].values

    # Scale data
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data)

    # Create sequences
    X, y = [], []
    for i in range(sequence_length, len(scaled_data)):
        X.append(scaled_data[i - sequence_length:i])
        y.append(scaled_data[i, 0])  # Predict the 'Close' price

    return np.array(X), np.array(y), scaler
