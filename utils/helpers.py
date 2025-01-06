import numpy as np
from typing import Dict, List, Any

def calculate_risk_score(beta: float, volatility: float) -> float:
    """
    Calculate risk score based on beta and volatility
    Returns score from 0 (lowest risk) to 1 (highest risk)
    """
    beta_score = min(abs(beta), 2) / 2  # Normalize beta to 0-1
    vol_score = min(volatility, 0.5) / 0.5  # Normalize volatility to 0-1
    return (beta_score + vol_score) / 2

def map_risk_preference(risk_level: str) -> tuple:
    """Map user risk preference to acceptable beta and volatility ranges"""
    risk_mappings = {
        'low': (0, 0.3),
        'medium': (0.3, 0.7),
        'high': (0.7, 1.0)
    }
    return risk_mappings[risk_level]

def calculate_return_score(historical_returns: float, target_return: float) -> float:
    """
    Score how well the stock's historical returns match the desired return
    Returns score from 0 (poor match) to 1 (perfect match)
    """
    diff = abs(historical_returns - target_return)
    return max(0, 1 - (diff / target_return))

def calculate_dividend_score(dividend_yield: float, priority: str) -> float:
    """
    Score dividend yield based on user's dividend priority
    Returns score from 0 (poor match) to 1 (perfect match)
    """
    priority_weights = {
        '0': 0,  # Not Important
        '1': 0.5,  # Somewhat Important
        '2': 1.0  # Very Important
    }
    
    weight = priority_weights[priority]
    if weight == 0:
        return 1.0  # If dividends aren't important, give full score
    
    # Score based on yield percentiles
    if dividend_yield == 0:
        return 0 if weight == 1.0 else 0.5
    elif dividend_yield > 6:
        return 0.7  # Penalize extremely high yields as they might be unsustainable
    else:
        return min(dividend_yield / 4, 1)  # Normalize against 4% as a "good" yield

def calculate_sector_score(stock_sector: str, preferred_sectors: List[str]) -> float:
    """
    Score how well the stock's sector matches user preferences
    Returns 1 if sector is preferred, 0 otherwise
    """
    return 1.0 if stock_sector.lower() in [s.lower() for s in preferred_sectors] else 0.0

def calculate_esg_score(esg_data: Dict[str, Any], ethical_considerations: List[str]) -> float:
    """
    Score how well the stock matches ethical considerations
    Returns score from 0 (poor match) to 1 (perfect match)
    """
    if not ethical_considerations:
        return 1.0  # If no ethical considerations specified, give full score
    
    scores = []
    for consideration in ethical_considerations:
        if consideration == 'esg':
            scores.append(esg_data.get('totalEsg', 0) / 100)
        elif consideration == 'green':
            scores.append(esg_data.get('environmentScore', 0) / 100)
        elif consideration == 'social':
            scores.append(esg_data.get('socialScore', 0) / 100)
        elif consideration == 'governance':
            scores.append(esg_data.get('governanceScore', 0) / 100)
    
    return np.mean(scores) if scores else 0.0

def calculate_investment_type_match(stock_info: Dict[str, Any], preferred_types: List[str]) -> float:
    """
    Determine if the investment type matches user preferences
    Returns 1 if type matches, 0 otherwise
    """
    # Map stock characteristics to investment types
    stock_types = set()
    
    # Basic stock
    stock_types.add('stocks')
    
    # Check if it might be considered for other categories
    if stock_info.get('marketCap', 0) > 10e9:  # Large cap
        stock_types.add('etf')  # Likely to be in major ETFs
    
    if stock_info.get('dividendYield', 0) > 0:
        stock_types.add('mutual_funds')  # Likely to be in dividend mutual funds
    
    return 1.0 if any(t in preferred_types for t in stock_types) else 0.0

def calculate_overall_score(
    stock_data: Dict[str, Any],
    user_preferences: Dict[str, Any]
) -> float:
    """
    Calculate overall matching score between stock and user preferences
    Returns score from 0 (poor match) to 1 (perfect match)
    """
    scores = {
        'risk': 0.0,
        'return': 0.0,
        'dividend': 0.0,
        'sector': 0.0,
        'ethical': 0.0,
        'type': 0.0
    }
    
    # Calculate individual scores
    risk_range = map_risk_preference(user_preferences['risk_level'])
    risk_score = calculate_risk_score(stock_data['beta'], stock_data['volatility'])
    scores['risk'] = 1 - abs(risk_score - np.mean(risk_range))
    
    scores['return'] = calculate_return_score(
        stock_data['historical_return'],
        user_preferences['desired_return']
    )
    
    scores['dividend'] = calculate_dividend_score(
        stock_data['dividend_yield'],
        user_preferences['dividend_priority']
    )
    
    scores['sector'] = calculate_sector_score(
        stock_data['sector'],
        user_preferences['sectors']
    )
    
    scores['ethical'] = calculate_esg_score(
        stock_data['esg_data'],
        user_preferences['ethical_considerations']
    )
    
    scores['type'] = calculate_investment_type_match(
        stock_data,
        user_preferences['investment_types']
    )
    
    # Weights for different components
    weights = {
        'risk': 0.25,
        'return': 0.25,
        'dividend': 0.15,
        'sector': 0.15,
        'ethical': 0.10,
        'type': 0.10
    }
    
    # Calculate weighted average
    total_score = sum(scores[k] * weights[k] for k in weights.keys())
    
    return total_score