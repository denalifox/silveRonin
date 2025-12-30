""
Market data fetcher for precious metals prices.
Supports multiple data sources with fallback mechanisms.
"""
import os
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, List, Tuple
import requests
from datetime import datetime, timezone
from dataclasses import dataclass
from loguru import logger


@dataclass
class MetalPrice:
    """Data class for storing metal price information."""
    symbol: str
    name: str
    price: float
    currency: str
    unit: str
    timestamp: float
    change_24h: Optional[float] = None
    change_pct_24h: Optional[float] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'symbol': self.symbol,
            'name': self.name,
            'price': self.price,
            'currency': self.currency,
            'unit': self.unit,
            'timestamp': self.timestamp,
            'change_24h': self.change_24h,
            'change_pct_24h': self.change_pct_24h,
            'formatted_price': self.formatted_price,
            'formatted_change': self.formatted_change
        }

    @property
    def formatted_price(self) -> str:
        """Format price with currency symbol and proper decimal places."""
        if self.currency == 'USD':
            return f"${self.price:,.2f}"
        return f"{self.price:,.2f} {self.currency}"

    @property
    def formatted_change(self) -> str:
        """Format 24h change with sign and percentage."""
        if self.change_24h is None or self.change_pct_24h is None:
            return "N/A"
        
        sign = '+' if self.change_24h >= 0 else ''
        return f"{sign}{self.change_24h:.2f} ({sign}{self.change_pct_24h:.2f}%)"


class MarketDataFetcher(ABC):
    """Abstract base class for market data fetchers."""
    
    def __init__(self, api_key: str = None):
        """Initialize with API key."""
        self.api_key = api_key or os.getenv('METALPRICE_API_KEY')
        if not self.api_key:
            logger.warning("No API key provided. Some features may be limited.")
    
    @abstractmethod
    def fetch_prices(self, metals: List[str] = None) -> Dict[str, MetalPrice]:
        ""Fetch current prices for the specified metals.""
        pass
    
    @abstractmethod
    def get_historical_data(self, metal: str, days: int = 30) -> List[Tuple[float, float]]:
        ""Fetch historical price data for a metal.""
        pass


class MetalPriceAPIFetcher(MarketDataFetcher):
    ""Fetches metal prices from MetalPriceAPI (https://metalpriceapi.com/)."""
    
    BASE_URL = "https://api.metalpriceapi.com/v1"
    
    # Map of metal symbols to their API codes and display names
    METAL_MAP = {
        'XAU': {'code': 'XAU', 'name': 'Gold', 'unit': 'oz'},
        'XAG': {'code': 'XAG', 'name': 'Silver', 'unit': 'oz'},
        'XPT': {'code': 'XPT', 'name': 'Platinum', 'unit': 'oz'},
        'XPD': {'code': 'XPD', 'name': 'Palladium', 'unit': 'oz'}
    }
    
    def __init__(self, api_key: str = None):
        """Initialize with API key."""
        super().__init__(api_key)
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
    
    def fetch_prices(self, metals: List[str] = None) -> Dict[str, MetalPrice]:
        ""Fetch current prices for the specified metals.""
        if not metals:
            metals = list(self.METAL_MAP.keys())
        
        prices = {}
        
        try:
            # Fetch all metals at once if possible
            response = self.session.get(
                f"{self.BASE_URL}/latest",
                params={
                    'api_key': self.api_key,
                    'base': 'USD',
                    'currencies': ','.join([f"X{metal}" for metal in metals if metal in self.METAL_MAP])
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            # Process the response
            timestamp = data.get('timestamp', time.time())
            
            for metal_code, price in data.get('rates', {}).items():
                # Skip base currency
                if metal_code == 'USD':
                    continue
                    
                # Extract the metal symbol (remove the 'X' prefix)
                symbol = metal_code[1:] if metal_code.startswith('X') else metal_code
                
                if symbol in self.METAL_MAP:
                    metal_info = self.METAL_MAP[symbol]
                    prices[symbol] = MetalPrice(
                        symbol=symbol,
                        name=metal_info['name'],
                        price=1.0 / price,  # Convert from USD per XAU to XAU per USD
                        currency='USD',
                        unit=metal_info['unit'],
                        timestamp=timestamp
                    )
            
            # Try to get 24h change if available
            self._update_24h_changes(prices)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching metal prices: {e}")
            # Fallback to individual requests if batch fails
            return self._fetch_prices_individually(metals)
        
        return prices
    
    def _fetch_prices_individually(self, metals: List[str]) -> Dict[str, MetalPrice]:
        ""Fallback method to fetch prices one by one.""
        prices = {}
        
        for metal in metals:
            if metal not in self.METAL_MAP:
                continue
                
            try:
                response = self.session.get(
                    f"{self.BASE_URL}/latest",
                    params={
                        'api_key': self.api_key,
                        'base': 'USD',
                        'currencies': f"X{metal}"
                    },
                    timeout=5
                )
                response.raise_for_status()
                data = response.json()
                
                price = list(data.get('rates', {}).values())[0]
                metal_info = self.METAL_MAP[metal]
                
                prices[metal] = MetalPrice(
                    symbol=metal,
                    name=metal_info['name'],
                    price=1.0 / price,  # Convert from USD per XAU to XAU per USD
                    currency='USD',
                    unit=metal_info['unit'],
                    timestamp=data.get('timestamp', time.time())
                )
                
            except (requests.exceptions.RequestException, (KeyError, IndexError)) as e:
                logger.error(f"Error fetching {metal} price: {e}")
        
        # Update 24h changes if we got any prices
        if prices:
            self._update_24h_changes(prices)
            
        return prices
    
    def _update_24h_changes(self, prices: Dict[str, MetalPrice]):
        ""Update 24h price changes for the given prices."""
        try:
            # Get historical data for 24 hours ago
            yesterday = int(time.time()) - 86400  # 24 hours in seconds
            
            for symbol, price in prices.items():
                if symbol not in self.METAL_MAP:
                    continue
                    
                try:
                    response = self.session.get(
                        f"{self.BASE_URL}/{yesterday}",
                        params={
                            'api_key': self.api_key,
                            'base': 'USD',
                            'currencies': f"X{symbol}"
                        },
                        timeout=5
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    if 'rates' in data and f"X{symbol}" in data['rates']:
                        old_price = 1.0 / data['rates'][f"X{symbol}"]
                        price.change_24h = price.price - old_price
                        price.change_pct_24h = (price.change_24h / old_price) * 100
                        
                except (requests.exceptions.RequestException, (KeyError, ZeroDivisionError)) as e:
                    logger.warning(f"Could not get 24h change for {symbol}: {e}")
                    
        except Exception as e:
            logger.error(f"Error updating 24h changes: {e}")
    
    def get_historical_data(self, metal: str, days: int = 30) -> List[Tuple[float, float]]:
        ""Fetch historical price data for a metal.""
        if metal not in self.METAL_MAP:
            raise ValueError(f"Unsupported metal: {metal}")
        
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        try:
            response = self.session.get(
                f"{self.BASE_URL}/timeframe",
                params={
                    'api_key': self.api_key,
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'base': 'USD',
                    'currencies': f"X{metal}"
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            # Process the response into (timestamp, price) pairs
            historical_data = []
            for date_str, rates in data.get('rates', {}).items():
                if f"X{metal}" in rates:
                    timestamp = datetime.strptime(date_str, '%Y-%m-%d').timestamp()
                    price = 1.0 / rates[f"X{metal}"]  # Convert from USD per XAU to XAU per USD
                    historical_data.append((timestamp, price))
            
            # Sort by timestamp
            historical_data.sort()
            return historical_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching historical data for {metal}: {e}")
            return []


# Default fetcher instance
market_data_fetcher = MetalPriceAPIFetcher()


def get_market_data_fetcher() -> MarketDataFetcher:
    ""Get the default market data fetcher instance."""
    return market_data_fetcher
