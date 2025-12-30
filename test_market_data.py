#!/usr/bin/env python3
"""Test script for the market data fetcher."""
import os
import sys
from dotenv import load_dotenv
from src.data_fetchers.market_data import get_market_data_fetcher, MetalPrice

def main():
    # Load environment variables
    load_dotenv()
    
    # Get the fetcher
    fetcher = get_market_data_fetcher()
    
    # Test fetching prices
    print("Fetching precious metals prices...")
    try:
        prices = fetcher.fetch_prices()
        
        if not prices:
            print("No prices returned. Check your API key and internet connection.")
            return
            
        print("\nCurrent Precious Metals Prices:")
        print("-" * 50)
        for symbol, price in prices.items():
            print(f"{price.name} ({symbol}): {price.formatted_price}")
            print(f"  24h Change: {price.formatted_change}")
            print(f"  Last Updated: {datetime.fromtimestamp(price.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 50)
            
        # Test historical data
        print("\nTesting historical data for Gold (XAU)...")
        historical = fetcher.get_historical_data('XAU', days=7)
        if historical:
            print(f"Got {len(historical)} data points for the last 7 days.")
            print(f"Latest: {historical[-1][1]:.2f} (on {datetime.fromtimestamp(historical[-1][0]).strftime('%Y-%m-%d')})")
            print(f"Oldest: {historical[0][1]:.2f} (on {datetime.fromtimestamp(historical[0][0]).strftime('%Y-%m-%d')})")
        else:
            print("No historical data available.")
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if "API key" in str(e):
            print("\nPlease set the METALPRICE_API_KEY environment variable or provide it in the .env file.")
            print("You can get a free API key from https://metalpriceapi.com/")

if __name__ == "__main__":
    from datetime import datetime  # Moved here to fix the error
    main()
