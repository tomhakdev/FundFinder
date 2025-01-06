import yfinance as yf
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from utils.cache_handler import CacheHandler

def get_investment_types(ticker_info: Dict[str, Any]) -> List[str]:
    """
    Determine all applicable investment types for a given security
    """
    types = set()
    quote_type = ticker_info.get('quoteType', '').lower()
    
    # Basic stock classification
    if quote_type in ['equity', 'stock', '']:
        types.add('stocks')
    
    # ETF classification
    if quote_type == 'etf':
        types.add('etf')
    
    # Mutual Fund classification
    if quote_type == 'mutualfund':
        types.add('mutual_funds')
    
    # Bond classification
    if quote_type == 'bond':
        types.add('bonds')
    
    # Large cap stocks are often components of major ETFs/mutual funds
    market_cap = ticker_info.get('marketCap', 0)
    if market_cap > 10e9:  # $10B+ market cap
        types.add('etf')
        types.add('mutual_funds')
    
    # Dividend stocks often appear in income-focused funds
    dividend_yield = ticker_info.get('dividendYield', 0)
    if dividend_yield > 0:
        types.add('mutual_funds')
    
    return list(types)

def fetch_stock_data(symbol: str, period='1y') -> Optional[pd.DataFrame]:
    """
    Fetch stock data from Yahoo Finance
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        df = df.reset_index()
        df = df.dropna()
        
        # Calculate additional technical indicators
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA50'] = df['Close'].rolling(window=50).mean()
        df['Daily_Return'] = df['Close'].pct_change()
        df['Volatility'] = df['Daily_Return'].rolling(window=20).std()
        
        return df
    except Exception as e:
        print(f"Error fetching data for {symbol}: {str(e)}")
        return None

def fetch_stock_details(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Fetch detailed stock information including ESG data
    """
    
    cache_handler = CacheHandler()
    
    # Try to get cached data first
    cached_data = cache_handler.get_cached_data(symbol)
    if cached_data:
        return cached_data

    try:
        # Manual sector mapping for commonly miscategorized stocks
        sector_overrides = {
            'GOOGL': 'tech',
            'GOOG': 'tech',
            'META': 'tech',
            'AMZN': 'tech',
            'NFLX': 'tech',
            'AAPL': 'tech',
            'MSFT': 'tech',
            'NVDA': 'tech',
            'AMD': 'tech',
            'INTC': 'tech',
            'CSCO': 'tech',
            'ADBE': 'tech',
            'CRM': 'tech',
            'TSLA': 'tech'
        }

        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Get historical data for returns calculation
        hist = ticker.history(period='1y')
        if hist.empty:
            print(f"No historical data found for {symbol}")
            return None
            
        # Calculate returns
        if len(hist['Close']) > 0:
            historical_return = ((hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1) * 100
            current_price = hist['Close'].iloc[-1]
            returns = hist['Close'].pct_change()
            volatility = returns.std() * np.sqrt(252) if len(returns) > 0 else 0
        else:
            print(f"No price data found for {symbol}")
            return None

        # Use sector override if available, otherwise use Yahoo's sector
        sector = sector_overrides.get(symbol, info.get('sector', 'Unknown')).lower()

        # Build stock data dictionary
        stock_data = {
            'symbol': symbol,
            'name': info.get('longName', symbol),
            'sector': sector,
            'industry': info.get('industry', 'Unknown'),
            'quoteType': info.get('quoteType', 'stock'),
            'beta': info.get('beta', 1.0),
            'marketCap': info.get('marketCap', 0),
            'regularMarketPrice': current_price,
            'dividend_yield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
            'historical_return': historical_return,
            'volatility': volatility,
            'esg_data': {
                'totalEsg': info.get('totalEsg', 0),
                'environmentScore': info.get('environmentScore', 0),
                'socialScore': info.get('socialScore', 0),
                'governanceScore': info.get('governanceScore', 0)
            }
        }
        
        print(f"\nFetched data for {symbol}:")
        print(f"Current Price: ${current_price:.2f}")
        print(f"Sector: {stock_data['sector']}")
        print(f"Historical Return: {historical_return:.2f}%")
        print(f"Beta: {stock_data['beta']}")
        
        cache_handler.save_to_cache(symbol, stock_data)
        return stock_data
        
    except Exception as e:
        print(f"Error fetching details for {symbol}: {str(e)}")
        return None

def get_stock_info(symbol: str) -> Optional[Dict[str, Any]]:
    """Get basic information about a stock"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        return {
            'name': info.get('longName', ''),
            'sector': info.get('sector', ''),
            'industry': info.get('industry', ''),
            'market_cap': info.get('marketCap', 0),
            'pe_ratio': info.get('forwardPE', 0),
            'dividend_yield': info.get('dividendYield', 0),
            'beta': info.get('beta', 0),
        }
    except Exception as e:
        print(f"Error fetching info for {symbol}: {str(e)}")
        return None

def calculate_piotroski_score(symbol: str) -> int:
    """Calculate the Piotroski F-Score for a given stock"""
    try:
        ticker = yf.Ticker(symbol)
        financials = ticker.financials
        balance_sheet = ticker.balance_sheet
        cash_flow = ticker.cashflow
        
        if any(df is None or df.empty for df in [financials, balance_sheet, cash_flow]):
            return 5
        
        score = 0
        
        # ROA and Cash Flow checks
        net_income = financials.loc['Net Income'].iloc[0]
        total_assets = balance_sheet.loc['Total Assets'].iloc[0]
        operating_cash_flow = cash_flow.loc['Operating Cash Flow'].iloc[0]
        
        if net_income > 0:
            score += 1
        if operating_cash_flow > 0:
            score += 1
        
        # Additional ratio checks...
        return score
    except Exception as e:
        print(f"Error calculating Piotroski score for {symbol}: {str(e)}")
        return 5

def get_sector_stocks(sector: str) -> List[str]:
    """Get list of stocks in a given sector"""
    sector_mapping = {
        'tech': [
            'AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'AMD', 'INTC', 'CSCO', 'ADBE', 'CRM',
            'TSM', 'AVGO', 'ORCL', 'ACN', 'ASML', 'TXN', 'QCOM', 'IBM', 'NOW', 'INTU',
            'ADI', 'MU', 'AMAT', 'LRCX', 'SNPS', 'CDNS', 'KLAC', 'PANW', 'WDAY', 'TEAM'
        ],
        'healthcare': [
            'JNJ', 'UNH', 'PFE', 'ABT', 'TMO', 'MRK', 'DHR', 'ABBV', 'BMY', 'AMGN',
            'LLY', 'CVS', 'ISRG', 'GILD', 'REGN', 'VRTX', 'MRNA', 'BIIB', 'ILMN', 'IDXX',
            'BSX', 'ZBH', 'BAX', 'EW', 'SGEN', 'HUM', 'CI', 'BDX', 'IQV', 'ZTS'
        ],
        'finance': [
            'JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'BLK', 'AXP', 'SPGI', 'CME',
            'SCHW', 'USB', 'PNC', 'TFC', 'AIG', 'MMC', 'AON', 'MET', 'PRU', 'ALL',
            'CB', 'PGR', 'TRV', 'AJG', 'FITB', 'SIVB', 'TROW', 'DFS', 'NTRS', 'STT'
        ],
        'energy': [
            'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'PXD', 'PSX', 'VLO', 'KMI', 'WMB',
            'MPC', 'OXY', 'DVN', 'HAL', 'BKR', 'HES', 'FANG', 'CVI', 'CTRA', 'MRO',
            'OKE', 'PSX', 'EPD', 'ET', 'TRGP', 'LNG', 'WMB', 'MPLX', 'CEQP', 'DCP'
        ],
        'consumer': [
            'PG', 'KO', 'PEP', 'WMT', 'COST', 'NKE', 'MCD', 'DIS', 'SBUX', 'HD',
            'TGT', 'LOW', 'EL', 'CL', 'KMB', 'GIS', 'K', 'HSY', 'KHC', 'STZ',
            'MDLZ', 'KR', 'SYY', 'TSN', 'CAG', 'HRL', 'MKC', 'CPB', 'SJM', 'TAP'
        ],
        'real_estate': [
            'AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'DLR', 'O', 'WELL', 'AVB', 'EQR',
            'SPG', 'VICI', 'INVH', 'MAA', 'UDR', 'ARE', 'BXP', 'VTR', 'HST', 'KIM',
            'REG', 'FRT', 'CPT', 'EXR', 'PEAK', 'HIW', 'DEI', 'SLG', 'ACC', 'AIV'
        ],
        'utilities': [
            'NEE', 'DUK', 'SO', 'D', 'AEP', 'EXC', 'SRE', 'XEL', 'WEC', 'ES',
            'ED', 'EIX', 'PEG', 'ETR', 'FE', 'AEE', 'CMS', 'CNP', 'DTE', 'PPL',
            'AES', 'AWK', 'LNT', 'EVRG', 'NI', 'PNW', 'NRG', 'IDA', 'ATO', 'OGE'
        ]
    }
    return sector_mapping.get(sector.lower(), [])


def get_sector_etfs(sector: str) -> List[str]:
    """Get list of ETFs for a given sector"""
    etf_mapping = {
        'tech': [
            'XLK',  # Technology Select Sector SPDR Fund
            'VGT',  # Vanguard Information Technology ETF
            'IYW',  # iShares U.S. Technology ETF
            'FTEC', # Fidelity MSCI Information Technology Index ETF
            'RYT',  # Invesco S&P 500 Equal Weight Technology ETF
            'QTEC', # First Trust NASDAQ-100 Technology Sector Index Fund
            'IGV',  # iShares Expanded Tech-Software Sector ETF
            'SOXX', # iShares Semiconductor ETF
            'SMH',  # VanEck Semiconductor ETF
            'ARKK', # ARK Innovation ETF
            'ARKW', # ARK Next Generation Internet ETF
            'QQQM', # Invesco NASDAQ 100 ETF
            'WCLD', # WisdomTree Cloud Computing Fund
            'AIQ',  # Global X Artificial Intelligence & Technology ETF
            'BOTZ'  # Global X Robotics & Artificial Intelligence ETF
        ],
        'healthcare': [
            'XLV',  # Health Care Select Sector SPDR Fund
            'VHT',  # Vanguard Health Care ETF
            'IYH',  # iShares U.S. Healthcare ETF
            'FHLC', # Fidelity MSCI Health Care Index ETF
            'RYH',  # Invesco S&P 500 Equal Weight Health Care ETF
            'IBB',  # iShares Biotechnology ETF
            'XBI',  # SPDR S&P Biotech ETF
            'ARKG', # ARK Genomic Revolution ETF
            'IHI',  # iShares U.S. Medical Devices ETF
            'GNOM'  # Global X Genomics & Biotechnology ETF
        ],
        'finance': [
            'XLF',   # Financial Select Sector SPDR Fund
            'VFH',   # Vanguard Financials ETF
            'IYF',   # iShares U.S. Financials ETF
            'FNCL',  # Fidelity MSCI Financials Index ETF
            'RYF',   # Invesco S&P 500 Equal Weight Financials ETF
            'KBE',   # SPDR S&P Bank ETF
            'KRE',   # SPDR S&P Regional Banking ETF
            'IAI',   # iShares U.S. Broker-Dealers & Securities Exchanges ETF
            'IYG',   # iShares U.S. Financial Services ETF
            'KBWB',  # Invesco KBW Bank ETF
            'FTXO',  # First Trust Nasdaq Bank ETF
            'QABA',  # First Trust NASDAQ ABA Community Bank Index Fund
            'DPST',  # Direxion Daily Regional Banks Bull 3X Shares
            'FINU',  # ProShares UltraPro Financial Select Sector
            'FINZ'   # ProShares UltraPro Short Financial Select Sector
        ],
        'energy': [
            'XLE',   # Energy Select Sector SPDR Fund
            'VDE',   # Vanguard Energy ETF
            'IYE',   # iShares U.S. Energy ETF
            'FENY',  # Fidelity MSCI Energy Index ETF
            'RYE',   # Invesco S&P 500 Equal Weight Energy ETF
            'PXE',   # Invesco Dynamic Energy Exploration & Production ETF
            'IEO',   # iShares U.S. Oil & Gas Exploration & Production ETF
            'PXJ',   # Invesco Dynamic Oil & Gas Services ETF
            'FILL',  # iShares MSCI Global Energy Producers ETF
            'ICLN',  # iShares Global Clean Energy ETF
            'TAN',   # Invesco Solar ETF
            'FAN',   # First Trust Global Wind Energy ETF
            'QCLN',  # First Trust NASDAQ Clean Edge Green Energy Index Fund
            'PBW',   # Invesco WilderHill Clean Energy ETF
            'ERTH'   # Invesco MSCI Sustainable Future ETF
        ],
        'consumer': [
            'XLP',   # Consumer Staples Select Sector SPDR Fund
            'VDC',   # Vanguard Consumer Staples ETF
            'IYK',   # iShares U.S. Consumer Goods ETF
            'FSTA',  # Fidelity MSCI Consumer Staples Index ETF
            'RHS',   # Invesco S&P 500 Equal Weight Consumer Staples ETF
            'XLY',   # Consumer Discretionary Select Sector SPDR Fund
            'VCR',   # Vanguard Consumer Discretionary ETF
            'IYC',   # iShares U.S. Consumer Discretionary ETF
            'FDIS',  # Fidelity MSCI Consumer Discretionary Index ETF
            'RCD',   # Invesco S&P 500 Equal Weight Consumer Discretionary ETF
            'PEZ',   # Invesco DWA Consumer Cyclicals Momentum ETF
            'IEDI',  # iShares Evolved U.S. Discretionary Spending ETF
            'WANT',  # Direxion Daily Consumer Discretionary Bull 3X Shares
            'PSL',   # Invesco DWA Consumer Staples Momentum ETF
            'FXG'    # First Trust Consumer Staples AlphaDEX Fund
        ],
        'real_estate': [
            'XLRE',  # Real Estate Select Sector SPDR Fund
            'VNQ',   # Vanguard Real Estate ETF
            'IYR',   # iShares U.S. Real Estate ETF
            'FREL',  # Fidelity MSCI Real Estate Index ETF
            'RWR',   # SPDR Dow Jones REIT ETF
            'SCHH',  # Schwab U.S. REIT ETF
            'ICF',   # iShares Cohen & Steers REIT ETF
            'USRT',  # iShares Core U.S. REIT ETF
            'REZ',   # iShares Residential Real Estate ETF
            'BBRE',  # JPMorgan BetaBuilders REIT ETF
            'RWX',   # SPDR Dow Jones International Real Estate ETF
            'MORT',  # VanEck Mortgage REIT Income ETF
            'SRET',  # Global X SuperDividend REIT ETF
            'ROOF',  # IQ U.S. Real Estate Small Cap ETF
            'NETL'   # NETLease Corporate Real Estate ETF
        ],
        'utilities': [
            'XLU',   # Utilities Select Sector SPDR Fund
            'VPU',   # Vanguard Utilities ETF
            'IDU',   # iShares U.S. Utilities ETF
            'FUTY',  # Fidelity MSCI Utilities Index ETF
            'RYU',   # Invesco S&P 500 Equal Weight Utilities ETF
            'PUI',   # Invesco DWA Utilities Momentum ETF
            'URA',   # Global X Uranium ETF
            'FXU',   # First Trust Utilities AlphaDEX Fund
            'PSCU',  # Invesco S&P SmallCap Utilities & Communication Services ETF
            'UTES',  # Virtus Reaves Utilities ETF
            'JHMU',  # John Hancock Multi-Factor Utilities ETF
            'UTSL',  # Direxion Daily Utilities Bull 3X Shares
            'PUI',   # Invesco DWA Utilities Momentum ETF
            'NLR',   # VanEck Uranium+Nuclear Energy ETF
            'KBUY'   # KraneShares Global Carbon ETF
        ]
    }
    return etf_mapping.get(sector.lower(), [])

def get_sector_mutual_funds(sector: str) -> List[str]:
    """Get comprehensive list of mutual funds for each sector"""
    fund_mapping = {
        'tech': [
            'FTECX', # Fidelity Technology Fund
            'FSPTX', # Fidelity Select Technology Portfolio
            'ROGSX', # Red Oak Technology Select Fund
            'PRGTX', # T. Rowe Price Global Technology Fund
            'JAGTX', # Janus Henderson Global Technology Fund
            'DTECX', # Delaware Technology Fund
            'PGTAX', # Putnam Global Technology Fund
            'FSCSX', # Fidelity Select Software & IT Services Portfolio
            'PRMTX', # T. Rowe Price Media & Telecommunications Fund
            'VITAX'  # Vanguard Information Technology Index Fund Admiral
        ],
        'healthcare': [
            'VGHCX', # Vanguard Health Care Fund
            'FSMEX', # Fidelity Select Medical Technology and Devices Portfolio
            'THIYX', # T. Rowe Price Health Sciences Fund
            'JAGLX', # Janus Henderson Global Life Sciences Fund
            'PHSTX', # Putnam Global Health Care Fund
            'FBIOX', # Fidelity Select Biotechnology Portfolio
            'FSHCX', # Fidelity Select Health Care Portfolio
            'PRHSX', # T. Rowe Price Health Sciences Fund
            'ETHSX', # Eaton Vance Worldwide Health Sciences Fund
            'VRHCX'  # Virtus Health Sciences Fund
        ],
        'finance': [
            'FSVLX',  # Fidelity Select Financial Services Portfolio
            'FSFXX',  # Fidelity Select Financial Services Portfolio
            'PRISX',  # T. Rowe Price Financial Services Fund
            'JNFSX',  # Janus Henderson Financial Services Fund
            'PFSAX',  # PGIM Financial Services Fund
            'VFAIX',  # Vanguard Financials Index Fund Admiral
            'RYFIX',  # Rydex Financial Services Fund
            'FSRBX',  # Fidelity Select Banking Portfolio
            'FIDSX',  # Fidelity Select Insurance Portfolio
            'KBWIX'   # Invesco KBW Bank ETF
        ],
        'energy': [
            'VGENX',  # Vanguard Energy Fund
            'FSENX',  # Fidelity Select Energy Portfolio
            'FANAX',  # Invesco Energy Fund
            'PRNEX',  # T. Rowe Price New Era Fund
            'MLPFX',  # Center Coast Brookfield MLP & Energy Infrastructure Fund
            'ICBAX',  # Invesco SteelPath MLP Income Fund
            'AMLPX',  # Alerian MLP Fund
            'EMLPX',  # First Trust North American Energy Infrastructure Fund
            'OIGLX',  # Oppenheimer SteelPath MLP Income Fund
            'ENPIX'   # Wells Fargo Utility and Telecommunications Fund
        ],
        'consumer': [
            'FSCPX',  # Fidelity Select Consumer Discretionary Portfolio
            'FCNSX',  # Fidelity Select Consumer Staples Portfolio
            'VCDAX',  # Vanguard Consumer Discretionary Index Fund Admiral
            'VCSAX',  # Vanguard Consumer Staples Index Fund Admiral
            'PRNHX',  # T. Rowe Price New Horizons Fund
            'PGCOX',  # PGIM Jennison Consumer Opportunities Fund
            'RYRTX',  # Rydex Retailing Fund
            'FSRPX',  # Fidelity Select Retailing Portfolio
            'FSUTX',  # Fidelity Select Consumer Finance Portfolio
            'FDFAX'   # Fidelity Select Consumer Staples Portfolio
        ],
        'real_estate': [
            'FRESX',  # Fidelity Real Estate Investment Portfolio
            'TRREX',  # T. Rowe Price Real Estate Fund
            'CSRSX',  # Cohen & Steers Realty Shares
            'VGSLX',  # Vanguard Real Estate Index Fund Admiral
            'DFREX',  # DFA Real Estate Securities Portfolio
            'JAREX',  # Nuveen Real Estate Securities Fund
            'FRIFX',  # Fidelity International Real Estate Fund
            'PRERX',  # Principal Real Estate Securities Fund
            'MRESX',  # Morgan Stanley Institutional Fund Trust - Real Estate Portfolio
            'CGMRX'   # CGM Realty Fund
        ],
        'utilities': [
            'FSUTX',  # Fidelity Select Utilities Portfolio
            'PRUAX',  # Putnam Global Utilities Fund
            'GAUIX',  # Gabelli Utilities Fund
            'VUIAX',  # Vanguard Utilities Index Fund Admiral
            'EVTMX',  # Eaton Vance Utilities Fund
            'FKUTX',  # Franklin Utilities Fund
            'MLUTX',  # MainStay MacKay Utilities Infrastructure Fund
            'GUTIX',  # Gabelli Utility Trust
            'UTIIX',  # John Hancock Utilities Fund
            'FIUIX'   # Fidelity Utilities Fund
        ]
    }
    return fund_mapping.get(sector.lower(), [])

def get_sector_bonds(sector: str) -> List[str]:
    """Get comprehensive list of sector-focused bonds"""
    bond_mapping = {
        'tech': [
            'VCIT',  # Vanguard Intermediate-Term Corporate Bond ETF
            'LQD',   # iShares iBoxx $ Investment Grade Corporate Bond ETF
            'IGLB',  # iShares Long-Term Corporate Bond ETF
            'USIG',  # iShares Broad USD Investment Grade Corporate Bond ETF
            'VCSH',  # Vanguard Short-Term Corporate Bond ETF
            'SPBO',  # SPDR Portfolio Corporate Bond ETF
            'IGIB',  # iShares Intermediate-Term Corporate Bond ETF
            'SPSB'   # SPDR Portfolio Short Term Corporate Bond ETF
        ],
        'healthcare': [
            'VGIT',  # Vanguard Intermediate-Term Treasury ETF
            'IEF',   # iShares 7-10 Year Treasury Bond ETF
            'SCHR',  # Schwab Intermediate-Term U.S. Treasury ETF
            'VGLT',  # Vanguard Long-Term Treasury ETF
            'TLH',   # iShares 10-20 Year Treasury Bond ETF
            'SPTL'   # SPDR Portfolio Long Term Treasury ETF
        ],
        'finance': [
            'AGG',    # iShares Core U.S. Aggregate Bond ETF
            'BND',    # Vanguard Total Bond Market ETF
            'VCIT',   # Vanguard Intermediate-Term Corporate Bond ETF
            'LQD',    # iShares iBoxx $ Investment Grade Corporate Bond ETF
            'VCSH',   # Vanguard Short-Term Corporate Bond ETF
            'HYG',    # iShares iBoxx $ High Yield Corporate Bond ETF
            'JNK',    # SPDR Bloomberg High Yield Bond ETF
            'MBB',    # iShares MBS ETF
            'TLT',    # iShares 20+ Year Treasury Bond ETF
            'SHY'     # iShares 1-3 Year Treasury Bond ETF
        ],
        'energy': [
            'EMLC',   # VanEck J.P. Morgan EM Local Currency Bond ETF
            'EMB',    # iShares J.P. Morgan USD Emerging Markets Bond ETF
            'PCY',    # Invesco Emerging Markets Sovereign Debt ETF
            'VWOB',   # Vanguard Emerging Markets Government Bond ETF
            'IGEM',   # iShares Interest Rate Hedged Emerging Markets Bond ETF
            'EMHY',   # iShares Emerging Markets High Yield Bond ETF
            'LEMB',   # iShares Emerging Markets Local Currency Bond ETF
            'EBND',   # SPDR Bloomberg Emerging Markets Local Bond ETF
            'ELD',    # WisdomTree Emerging Markets Local Debt Fund
            'EMLP'    # First Trust North American Energy Infrastructure Fund
        ],
        'consumer': [
            'MUB',    # iShares National Muni Bond ETF
            'TFI',    # SPDR Nuveen Bloomberg Municipal Bond ETF
            'ITM',    # VanEck Intermediate Muni ETF
            'SUB',    # iShares Short-Term National Muni Bond ETF
            'PZA',    # Invesco National AMT-Free Municipal Bond ETF
            'SHM',    # SPDR Nuveen Bloomberg Short Term Municipal Bond ETF
            'VTEB',   # Vanguard Tax-Exempt Bond ETF
            'MLN',    # VanEck Long Muni ETF
            'MMIN',   # IQ MacKay Municipal Insured ETF
            'BCHG'    # Blackrock Credit Allocation Income Trust
        ],
        'real_estate': [
            'CMBS',   # iShares CMBS ETF
            'REM',    # iShares Mortgage Real Estate ETF
            'MORT',   # VanEck Mortgage REIT Income ETF
            'VMBS',   # Vanguard Mortgage-Backed Securities ETF
            'GNMA',   # iShares GNMA Bond ETF
            'SRET',   # Global X SuperDividend REIT ETF
            'ROOF',   # IQ U.S. Real Estate Small Cap ETF
            'NETL',   # NETLease Corporate Real Estate ETF
            'VNQ',    # Vanguard Real Estate ETF
            'IYR'     # iShares U.S. Real Estate ETF
        ],
        'utilities': [
            'BAB',    # Invesco Taxable Municipal Bond ETF
            'BABS',   # SPDR Nuveen Bloomberg Build America Bond ETF
            'GBAB',   # Guggenheim Taxable Municipal Bond & Investment Grade Debt Trust
            'BTT',    # BlackRock Municipal 2030 Target Term Trust
            'BKN',    # BlackRock Investment Quality Municipal Trust
            'BTA',    # BlackRock Long-Term Municipal Advantage Trust
            'BFK',    # BlackRock Municipal Income Trust
            'BLE',    # BlackRock Municipal Income Trust II
            'MUC',    # BlackRock MuniHoldings California Quality Fund
            'MUH'     # BlackRock MuniHoldings Fund II
        ]
    }
    return bond_mapping.get(sector.lower(), [])

def standardize_sector(sector: str) -> str:
    """Standardize sector names"""
    sector_map = {
        'technology': 'tech',
        'information technology': 'tech',
        'it services': 'tech',
        'semiconductors': 'tech',
        'software': 'tech',
        'communication services': 'tech',
        'internet content & information': 'tech',
        'electronic components': 'tech',
        'semiconductor equipment & materials': 'tech',
        'computer hardware': 'tech'
    }
    return sector_map.get(sector.lower(), sector.lower())

def matches_investment_criteria(stock_data: Dict[str, Any], user_preferences: Dict[str, Any]) -> bool:
    """Check if stock matches investment criteria with more flexible matching"""
    
    print(f"\nChecking criteria for {stock_data.get('symbol')}:")
    
    # Investment Type Check
    stock_types = get_investment_types(stock_data)
    valid_types = set(user_preferences.get('investment_types', ['stocks']))
    if not valid_types:
        valid_types = {'stocks'}
    print(f"Stock types: {stock_types}, Valid types: {valid_types}")
    
    if not any(t in valid_types for t in stock_types):
        print("Failed investment type check")
        return False

    # Sector Check - Use standardized sectors
    stock_sector = standardize_sector(stock_data.get('sector', ''))
    valid_sectors = [standardize_sector(s) for s in user_preferences['sectors']]
    print(f"Stock sector: {stock_sector}, Valid sectors: {valid_sectors}")
    
    if stock_sector not in valid_sectors:
        print("Failed sector check")
        return False

    # Risk Level Check
    beta = stock_data.get('beta', 1.0)
    risk_ranges = {
        'low': (-float('inf'), 1.1),
        'medium': (0.7, 1.4),
        'high': (0.9, float('inf'))
    }
    risk_range = risk_ranges[user_preferences['risk_level']]
    print(f"Beta: {beta}, Required range: {risk_range}")
    
    if not (risk_range[0] <= beta <= risk_range[1]):
        print("Failed risk level check")
        return False

    # Return Check - Handle nan values
    target_return = float(user_preferences['desired_return'])
    historical_return = stock_data.get('historical_return', 0)
    print(f"Historical return: {historical_return}%, Target return: {target_return}%")
    
    if pd.isna(historical_return):
        historical_return = 0  # Default to 0 for unknown returns
    
    # More lenient return check - allow if it's at least 25% of target
    if historical_return < target_return * 0.25:
        print("Failed return check")
        return False

    # Dividend Check - More lenient for high priority
    dividend_yield = stock_data.get('dividend_yield', 0)
    priority = user_preferences['dividend_priority']
    print(f"Dividend yield: {dividend_yield}%, Priority: {priority}")
    
    if priority == '2' and dividend_yield < 1.5:  # Reduced from 2%
        print("Failed dividend check")
        return False
    elif priority == '1' and dividend_yield < 0.3:
        print("Failed dividend check")
        return False

    print("All checks passed!")
    return True

def get_recommendations(user_preferences: Dict[str, Any], num_recommendations: int = 5) -> Optional[List[Dict[str, Any]]]:
    """
    Get stock recommendations strictly matching user preferences
    """
    try:
        print("\nStarting recommendation search...")
        print(f"User preferences: {user_preferences}")
        
        # Get candidate stocks
        candidate_symbols = []
        for sector in user_preferences['sectors']:
            sector_stocks = get_sector_stocks(sector)
            if 'etf' in user_preferences.get('investment_types', []):
                sector_stocks.extend(get_sector_etfs(sector))
            candidate_symbols.extend(sector_stocks)

        candidate_symbols = list(set(candidate_symbols))
        print(f"\nFound {len(candidate_symbols)} candidate symbols: {candidate_symbols}")
        
        # Get matching stocks
        qualified_stocks = []
        for symbol in candidate_symbols:
            print(f"\nAnalyzing {symbol}...")
            stock_data = fetch_stock_details(symbol)
            if not stock_data:
                continue
                
            if matches_investment_criteria(stock_data, user_preferences):
                score = calculate_overall_score(stock_data, user_preferences)
                qualified_stocks.append((score, stock_data))

        print(f"\nFound {len(qualified_stocks)} qualified stocks")
        
        if not qualified_stocks:
            return None
            
        qualified_stocks.sort(reverse=True, key=lambda x: x[0])
        recommendations = [stock for _, stock in qualified_stocks[:num_recommendations]]
        
        return recommendations

    except Exception as e:
        print(f"Error in get_recommendations: {str(e)}")
        return None
    

def calculate_overall_score(stock_data: Dict[str, Any], user_preferences: Dict[str, Any]) -> float:
    """Calculate matching score between stock and user preferences"""
    weights = {
        'risk': 0.25,
        'return': 0.30,
        'sector': 0.20,
        'dividend': 0.15,
        'ethical': 0.05,
        'budget': 0.05
    }
    
    scores = {}
    
    # Risk Score - Improved to be more nuanced
    beta = stock_data.get('beta', 1.0)
    if user_preferences['risk_level'] == 'high':
        scores['risk'] = min(beta / 2, 1.0)  # Higher beta = better for high risk
    elif user_preferences['risk_level'] == 'medium':
        scores['risk'] = 1.0 - abs(beta - 1.0)  # Closer to 1.0 = better for medium risk
    else:  # low risk
        scores['risk'] = max(0, 1.0 - (beta / 2))  # Lower beta = better for low risk

    
    # Return Score - Much more lenient
    target_return = float(user_preferences['desired_return'])
    hist_return = stock_data.get('historical_return', 0)
    if pd.isna(hist_return):
        scores['return'] = 0.5  # Default score for unknown returns
    elif hist_return >= target_return:
        scores['return'] = 1.0  # Full score for meeting or exceeding target
    else:
        # Partial score for returns between 25% and 100% of target
        scores['return'] = max(0.5, hist_return / target_return)
    
    # Sector Score - Standardized matching
    stock_sector = standardize_sector(stock_data.get('sector', ''))
    valid_sectors = [standardize_sector(s) for s in user_preferences['sectors']]
    scores['sector'] = 1.0 if stock_sector in valid_sectors else 0.0
    
    # Dividend Score
    div_yield = stock_data.get('dividend_yield', 0)
    if user_preferences['dividend_priority'] == '2':
        scores['dividend'] = min(div_yield / 2.0, 1.0)
    elif user_preferences['dividend_priority'] == '1':
        scores['dividend'] = min(div_yield / 1.0, 1.0)
    else:
        scores['dividend'] = 1.0
    
    if user_preferences.get('ethical_considerations'):
        esg_data = stock_data.get('esg_data', {})
        ethical_scores = []
        for consideration in user_preferences['ethical_considerations']:
            if consideration == 'esg':
                ethical_scores.append(esg_data.get('totalEsg', 0) / 100)
            elif consideration == 'green':
                ethical_scores.append(esg_data.get('environmentScore', 0) / 100)
            elif consideration == 'social':
                ethical_scores.append(esg_data.get('socialScore', 0) / 100)
            elif consideration == 'governance':
                ethical_scores.append(esg_data.get('governanceScore', 0) / 100)
        scores['ethical'] = np.mean(ethical_scores) if ethical_scores else 0.0
    else:
        scores['ethical'] = 1.0
        
    # Budget score is always 1.0 since we allow multiple units
    scores['budget'] = 1.0
    
    # Calculate weighted average
    final_score = sum(scores[k] * weights[k] for k in weights.keys())
    
    # Print detailed scoring information
    print(f"\nDetailed scores for {stock_data.get('symbol')}:")
    for criterion, score in scores.items():
        print(f"{criterion}: {score:.3f}")
    print(f"Final score: {final_score:.3f}")
    
    return final_score

# Additional helper function for technical analysis
def calculate_technical_indicators(historical_data: pd.DataFrame) -> Dict[str, float]:
    """Calculate additional technical indicators for analysis"""
    if historical_data is None or historical_data.empty:
        return {}
        
    indicators = {}
    
    # RSI (14-day)
    delta = historical_data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    indicators['rsi'] = 100 - (100 / (1 + rs.iloc[-1]))
    
    # MACD
    exp1 = historical_data['Close'].ewm(span=12, adjust=False).mean()
    exp2 = historical_data['Close'].ewm(span=26, adjust=False).mean()
    indicators['macd'] = exp1.iloc[-1] - exp2.iloc[-1]
    
    # Bollinger Bands
    sma = historical_data['Close'].rolling(window=20).mean()
    std = historical_data['Close'].rolling(window=20).std()
    indicators['bollinger_upper'] = sma + (std * 2)
    indicators['bollinger_lower'] = sma - (std * 2)
    
    return indicators