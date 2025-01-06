from flask import render_template, redirect, url_for, jsonify, session, flash, request
from flask import current_app as app
from app import db
from app.forms import InvestmentForm
from utils.data_fetcher import fetch_stock_data, calculate_piotroski_score, get_stock_info, get_recommendations
from models.lstm_model import StockPredictor
import random

# Create a global predictor instance
predictor = StockPredictor()

@app.route('/projections/<symbol>')
def projections(symbol):
    # Fetch historical data
    historical_data = fetch_stock_data(symbol)
    if historical_data is None:
        flash(f"Unable to fetch data for {symbol}")
        return redirect(url_for('recommendations'))
    
    # Get stock info and Piotroski score
    stock_info = get_stock_info(symbol)
    piotroski_score = calculate_piotroski_score(symbol)
    
    # Train model and get predictions
    try:
        predictor.train(historical_data)
        future_predictions = predictor.predict_future(historical_data)
        
        # Convert predictions to list format for JSON serialization
        predictions_data = [
            {'date': str(date), 'price': price} 
            for date, price in future_predictions.items()
        ]
    except Exception as e:
        print(f"Error making predictions: {str(e)}")
        flash(f"Error generating predictions: {str(e)}")
        predictions_data = []
    
    return render_template('projections.html',
                         symbol=symbol,
                         historical_data=historical_data.to_dict('records'),
                         predictions_data=predictions_data,
                         piotroski_score=piotroski_score,
                         stock_info=stock_info)

@app.route('/', methods=['GET', 'POST'])
def index():
    form = InvestmentForm()
    if form.validate_on_submit():
        # Ensure investment_types is not empty
        if not form.investment_types.data:
            form.investment_types.data = ['stocks']  # Default to stocks if none selected
            
        session['investment_params'] = {
            'risk_level': form.risk_level.data,
            'desired_return': float(form.desired_return.data),
            'duration': int(form.duration.data),
            'sectors': form.sectors.data,
            'budget': float(form.budget.data),
            'dividend_priority': form.dividend_priority.data,
            'ethical_considerations': form.ethical_considerations.data,
            'investment_types': form.investment_types.data
        }
        return redirect(url_for('recommendations'))
    
    if request.method == 'POST':
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", "error")
    
    return render_template('index.html', form=form)


from flask import render_template, redirect, url_for, jsonify, session, flash
from flask import current_app as app
from app import db
from app.forms import InvestmentForm
from utils.data_fetcher import get_recommendations
import random

@app.route('/recommendations')
def recommendations():
    if 'investment_params' not in session:
        flash("Please fill out the investment profile form first.", "error")
        return redirect(url_for('index'))
    
    params = session['investment_params']
    print("\nProcessing recommendation request with parameters:", params)
    
    recommendations = get_recommendations(params)
    
    if recommendations is None or len(recommendations) == 0:
        flash("No investments found that match your criteria. Try adjusting your preferences for more options.", "warning")
        return render_template('recommendations.html', 
                             recommendations=[],
                             preferences=params,
                             no_results=True)
    
    print(f"\nFound {len(recommendations)} recommendations")
    for i, rec in enumerate(recommendations, 1):
        print(f"\nRecommendation {i}:")
        print(f"Symbol: {rec['symbol']}")
        print(f"Name: {rec['name']}")
        print(f"Sector: {rec['sector']}")
        print(f"Current Price: ${rec.get('regularMarketPrice', 'N/A')}")
        print(f"Historical Return: {rec.get('historical_return', 'N/A')}%")
        print(f"Beta: {rec.get('beta', 'N/A')}")
        print(f"Dividend Yield: {rec.get('dividend_yield', 'N/A')}%")
    
    return render_template('recommendations.html', 
                         recommendations=recommendations,
                         preferences=params,
                         no_results=False)

@app.route('/shuffle')
def shuffle_recommendations():
    if 'investment_params' not in session:
        return redirect(url_for('index'))
    
    params = session['investment_params']
    recommendations = get_recommendations(params)
    
    if recommendations is None:
        return jsonify({
            'error': 'No matching investments found',
            'recommendations': []
        }), 404
    
    return jsonify({
        'error': None,
        'recommendations': recommendations
    })

def generate_recommendations(params):
    # This would be replaced with your actual recommendation logic
    # For now, returning dummy data
    stocks = [
        {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology"},
        {"symbol": "MSFT", "name": "Microsoft Corp.", "sector": "Technology"},
        {"symbol": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare"},
        {"symbol": "V", "name": "Visa Inc.", "sector": "Financial"},
        {"symbol": "PG", "name": "Procter & Gamble", "sector": "Consumer Goods"}
    ]
    return random.sample(stocks, 5)