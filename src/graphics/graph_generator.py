"""
Graph generator for real-time precious metals price visualization.
Creates dynamic charts with market hours highlighting and live updates.
"""
import os
import time
import logging
from typing import Dict, List, Optional, Tuple
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from datetime import datetime, timedelta, timezone
import pytz
from dataclasses import dataclass
from loguru import logger
import json

from ..data_fetchers.market_data import MetalPrice, get_market_data_fetcher

@dataclass
class MarketHours:
    """Market hours configuration."""
    name: str
    timezone: str
    open_hour: int  # UTC hour
    close_hour: int  # UTC hour
    color: str
    alpha: float = 0.2

class GraphGenerator:
    """Generates real-time graphs for precious metals prices."""
    
    def __init__(self, output_dir: str = "assets/images"):
        """Initialize the graph generator.
        
        Args:
            output_dir: Directory to save generated graphs
        """
        self.output_dir = output_dir
        self.market_data_fetcher = get_market_data_fetcher()
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Market hours configuration
        self.market_hours = [
            MarketHours("NY", "America/New_York", 13, 18, "#FF6B6B", 0.15),  # 8 AM - 1 PM ET
            MarketHours("London", "Europe/London", 8, 15, "#4ECDC4", 0.15),   # 8 AM - 3 PM GMT
            MarketHours("Shanghai", "Asia/Shanghai", 1, 7, "#45B7D1", 0.15),   # 9 AM - 3 PM CST
            MarketHours("Tokyo", "Asia/Tokyo", 0, 6, "#96CEB4", 0.15),        # 9 AM - 3 PM JST
        ]
        
        # Graph styling
        self.setup_matplotlib_style()
        
        # Cache for historical data
        self.price_history = {}
        self.max_history_points = 100  # Keep last 100 data points
        
        # Output files
        self.current_prices_file = os.path.join(output_dir, "current_prices.png")
        self.price_history_file = os.path.join(output_dir, "price_history.png")
        self.market_overview_file = os.path.join(output_dir, "market_overview.png")
    
    def setup_matplotlib_style(self):
        """Set up matplotlib styling for professional appearance."""
        plt.style.use('dark_background')
        
        # Custom colors
        self.colors = {
            'gold': '#FFD700',
            'silver': '#C0C0C0',
            'platinum': '#E5E4E2',
            'palladium': '#B59410',
            'background': '#1a1a1a',
            'text': '#FFFFFF',
            'grid': '#333333',
            'positive': '#00FF00',
            'negative': '#FF0000'
        }
        
        # Set default parameters
        plt.rcParams.update({
            'figure.facecolor': self.colors['background'],
            'axes.facecolor': self.colors['background'],
            'axes.edgecolor': self.colors['text'],
            'axes.labelcolor': self.colors['text'],
            'text.color': self.colors['text'],
            'xtick.color': self.colors['text'],
            'ytick.color': self.colors['text'],
            'grid.color': self.colors['grid'],
            'grid.alpha': 0.3,
            'font.family': 'Arial',
            'font.size': 10,
            'axes.titlesize': 14,
            'axes.labelsize': 12,
            'figure.titlesize': 16,
        })
    
    def get_current_utc_time(self) -> datetime:
        """Get current UTC time."""
        return datetime.now(timezone.utc)
    
    def is_market_open(self, market: MarketHours) -> bool:
        """Check if a market is currently open."""
        now = self.get_current_utc_time()
        return market.open_hour <= now.hour < market.close_hour
    
    def add_market_hours_background(self, ax, start_time: datetime, end_time: datetime):
        """Add colored backgrounds for market hours."""
        for market in self.market_hours:
            # Convert market hours to UTC
            market_tz = pytz.timezone(market.timezone)
            
            # Create time range for the graph
            time_range = []
            current = start_time
            while current <= end_time:
                time_range.append(current)
                current += timedelta(hours=1)
            
            # Find market hours within the time range
            for dt in time_range:
                dt_local = dt.astimezone(market_tz)
                if market.open_hour <= dt_local.hour < market.close_hour:
                    ax.axvspan(dt, dt + timedelta(hours=1), 
                             alpha=market.alpha, color=market.color, zorder=0)
    
    def update_price_history(self, prices: Dict[str, MetalPrice]):
        """Update the price history cache."""
        current_time = self.get_current_utc_time()
        
        for symbol, price in prices.items():
            if symbol not in self.price_history:
                self.price_history[symbol] = []
            
            # Add new data point
            self.price_history[symbol].append((current_time, price.price))
            
            # Keep only the last N points
            if len(self.price_history[symbol]) > self.max_history_points:
                self.price_history[symbol] = self.price_history[symbol][-self.max_history_points:]
    
    def generate_current_prices_graph(self, prices: Dict[str, MetalPrice]) -> str:
        """Generate a graph showing current prices with 24h changes."""
        if not prices:
            logger.warning("No price data available for current prices graph")
            return self.current_prices_file
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), 
                                        gridspec_kw={'height_ratios': [3, 1]})
        fig.suptitle('Precious Metals - Current Prices', fontsize=16, fontweight='bold')
        
        # Extract data
        symbols = list(prices.keys())
        current_prices = [prices[sym].price for sym in symbols]
        changes_24h = [prices[sym].change_24h or 0 for sym in symbols]
        
        # Color mapping
        symbol_colors = {
            'XAU': self.colors['gold'],
            'XAG': self.colors['silver'],
            'XPT': self.colors['platinum'],
            'XPD': self.colors['palladium']
        }
        
        colors = [symbol_colors.get(sym, '#FFFFFF') for sym in symbols]
        
        # Bar chart for current prices
        bars = ax1.bar(symbols, current_prices, color=colors, alpha=0.8, edgecolor='white', linewidth=2)
        
        # Add value labels on bars
        for bar, price in zip(bars, current_prices):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                    f'${price:,.2f}', ha='center', va='bottom', fontweight='bold')
        
        ax1.set_ylabel('Price (USD)', fontsize=12)
        ax1.set_title('Current Spot Prices', fontsize=14)
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(bottom=0)
        
        # Bar chart for 24h changes
        change_colors = [self.colors['positive'] if change >= 0 else self.colors['negative'] 
                        for change in changes_24h]
        
        bars2 = ax2.bar(symbols, changes_24h, color=change_colors, alpha=0.8, edgecolor='white', linewidth=1)
        
        # Add percentage labels
        for bar, change, price in zip(bars2, changes_24h, current_prices):
            height = bar.get_height()
            pct_change = (change / (price - change)) * 100 if price != change else 0
            ax2.text(bar.get_x() + bar.get_width()/2., 
                    height + (0.01 if height >= 0 else -0.01),
                    f'{pct_change:+.2f}%', ha='center', 
                    va='bottom' if height >= 0 else 'top', fontweight='bold')
        
        ax2.set_ylabel('24h Change (USD)', fontsize=12)
        ax2.set_title('24 Hour Changes', fontsize=14)
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='white', linestyle='-', alpha=0.5)
        
        # Add market status
        now = self.get_current_utc_time()
        open_markets = [m.name for m in self.market_hours if self.is_market_open(m)]
        status_text = f"Markets Open: {', '.join(open_markets) if open_markets else 'None'}"
        fig.text(0.5, 0.02, status_text, ha='center', fontsize=10, 
                style='italic', color=self.colors['text'])
        
        # Add timestamp
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S UTC')
        fig.text(0.99, 0.02, f'Updated: {timestamp}', ha='right', fontsize=9, 
                style='italic', color=self.colors['text'])
        
        plt.tight_layout()
        plt.savefig(self.current_prices_file, dpi=100, bbox_inches='tight', 
                   facecolor=self.colors['background'])
        plt.close()
        
        logger.info(f"Generated current prices graph: {self.current_prices_file}")
        return self.current_prices_file
    
    def generate_price_history_graph(self, hours: int = 24) -> str:
        """Generate a graph showing price history over the specified hours."""
        if not self.price_history:
            logger.warning("No price history available")
            return self.price_history_file
        
        # Create figure
        fig, ax = plt.subplots(figsize=(14, 8))
        fig.suptitle(f'Precious Metals - Price History (Last {hours} Hours)', 
                    fontsize=16, fontweight='bold')
        
        # Calculate time range
        end_time = self.get_current_utc_time()
        start_time = end_time - timedelta(hours=hours)
        
        # Add market hours background
        self.add_market_hours_background(ax, start_time, end_time)
        
        # Plot each metal's price history
        symbol_colors = {
            'XAU': self.colors['gold'],
            'XAG': self.colors['silver'],
            'XPT': self.colors['platinum'],
            'XPD': self.colors['palladium']
        }
        
        symbol_names = {
            'XAU': 'Gold',
            'XAG': 'Silver',
            'XPT': 'Platinum',
            'XPD': 'Palladium'
        }
        
        for symbol, history in self.price_history.items():
            if not history:
                continue
            
            # Filter data within time range
            filtered_data = [(t, p) for t, p in history if t >= start_time]
            if not filtered_data:
                continue
            
            times, prices = zip(*filtered_data)
            color = symbol_colors.get(symbol, '#FFFFFF')
            name = symbol_names.get(symbol, symbol)
            
            ax.plot(times, prices, color=color, linewidth=2, label=name, alpha=0.9)
            
            # Add latest price annotation
            latest_time, latest_price = filtered_data[-1]
            ax.annotate(f'{name}: ${latest_price:.2f}',
                       xy=(latest_time, latest_price),
                       xytext=(10, 5), textcoords='offset points',
                       color=color, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.3))
        
        # Formatting
        ax.set_xlabel('Time (UTC)', fontsize=12)
        ax.set_ylabel('Price (USD)', fontsize=12)
        ax.set_title('Price Trends', fontsize=14)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left', framealpha=0.9)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # Add market legend
        legend_elements = []
        for market in self.market_hours:
            is_open = self.is_market_open(market)
            status = "OPEN" if is_open else "CLOSED"
            alpha = 1.0 if is_open else 0.3
            legend_elements.append(plt.Rectangle((0, 0), 1, 1, fc=market.color, 
                                               alpha=market.alpha, label=f'{market.name} {status}'))
        
        ax.legend(handles=legend_elements, loc='upper right', framealpha=0.9)
        
        # Add timestamp
        timestamp = self.get_current_utc_time().strftime('%Y-%m-%d %H:%M:%S UTC')
        fig.text(0.99, 0.02, f'Updated: {timestamp}', ha='right', fontsize=9, 
                style='italic', color=self.colors['text'])
        
        plt.tight_layout()
        plt.savefig(self.price_history_file, dpi=100, bbox_inches='tight', 
                   facecolor=self.colors['background'])
        plt.close()
        
        logger.info(f"Generated price history graph: {self.price_history_file}")
        return self.price_history_file
    
    def generate_market_overview(self) -> str:
        """Generate a comprehensive market overview dashboard."""
        # Get current prices
        prices = self.market_data_fetcher.fetch_prices()
        
        if not prices:
            logger.warning("No price data available for market overview")
            return self.market_overview_file
        
        # Create figure with subplots
        fig = plt.figure(figsize=(16, 10))
        fig.suptitle('Precious Metals Market Overview', fontsize=18, fontweight='bold')
        
        # Create grid layout
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # 1. Current prices (top, spanning 2 columns)
        ax1 = fig.add_subplot(gs[0, :2])
        self._plot_mini_prices(ax1, prices)
        
        # 2. Market status (top right)
        ax2 = fig.add_subplot(gs[0, 2])
        self._plot_market_status(ax2)
        
        # 3. Price history (middle, spanning all columns)
        ax3 = fig.add_subplot(gs[1, :])
        self._plot_mini_history(ax3, hours=12)
        
        # 4. 24h changes (bottom left)
        ax4 = fig.add_subplot(gs[2, 0])
        self._plot_changes(ax4, prices, '24h')
        
        # 5. Volume indicator (bottom middle)
        ax5 = fig.add_subplot(gs[2, 1])
        self._plot_volume_indicator(ax5)
        
        # 6. News ticker preview (bottom right)
        ax6 = fig.add_subplot(gs[2, 2])
        self._plot_news_preview(ax6)
        
        # Add timestamp
        timestamp = self.get_current_utc_time().strftime('%Y-%m-%d %H:%M:%S UTC')
        fig.text(0.99, 0.01, f'Updated: {timestamp}', ha='right', fontsize=9, 
                style='italic', color=self.colors['text'])
        
        plt.tight_layout()
        plt.savefig(self.market_overview_file, dpi=100, bbox_inches='tight', 
                   facecolor=self.colors['background'])
        plt.close()
        
        logger.info(f"Generated market overview: {self.market_overview_file}")
        return self.market_overview_file
    
    def _plot_mini_prices(self, ax, prices):
        """Plot mini current prices display."""
        symbols = list(prices.keys())
        current_prices = [prices[sym].price for sym in symbols]
        
        symbol_colors = {
            'XAU': self.colors['gold'],
            'XAG': self.colors['silver'],
            'XPT': self.colors['platinum'],
            'XPD': self.colors['palladium']
        }
        
        colors = [symbol_colors.get(sym, '#FFFFFF') for sym in symbols]
        symbol_names = ['Gold', 'Silver', 'Platinum', 'Palladium']
        
        bars = ax.bar(symbol_names, current_prices, color=colors, alpha=0.8)
        ax.set_title('Current Prices', fontsize=12, fontweight='bold')
        ax.set_ylabel('USD', fontsize=10)
        
        # Add value labels
        for bar, price in zip(bars, current_prices):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                   f'${price:,.2f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    def _plot_market_status(self, ax):
        """Plot market status indicators."""
        ax.set_title('Market Status', fontsize=12, fontweight='bold')
        ax.axis('off')
        
        y_pos = 0.9
        for market in self.market_hours:
            is_open = self.is_market_open(market)
            status = "● OPEN" if is_open else "○ CLOSED"
            color = market.color if is_open else '#666666'
            
            ax.text(0.5, y_pos, f'{market.name}: {status}', 
                   ha='center', va='center', fontsize=10,
                   color=color, fontweight='bold' if is_open else 'normal')
            y_pos -= 0.25
    
    def _plot_mini_history(self, ax, hours):
        """Plot mini price history."""
        if not self.price_history:
            ax.text(0.5, 0.5, 'No history data', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=12)
            return
        
        end_time = self.get_current_utc_time()
        start_time = end_time - timedelta(hours=hours)
        
        symbol_colors = {
            'XAU': self.colors['gold'],
            'XAG': self.colors['silver'],
            'XPT': self.colors['platinum'],
            'XPD': self.colors['palladium']
        }
        
        symbol_names = {
            'XAU': 'Gold',
            'XAG': 'Silver',
            'XPT': 'Platinum',
            'XPD': 'Palladium'
        }
        
        for symbol, history in self.price_history.items():
            if not history:
                continue
            
            filtered_data = [(t, p) for t, p in history if t >= start_time]
            if not filtered_data:
                continue
            
            times, prices = zip(*filtered_data)
            color = symbol_colors.get(symbol, '#FFFFFF')
            name = symbol_names.get(symbol, symbol)
            
            ax.plot(times, prices, color=color, linewidth=2, label=name, alpha=0.9)
        
        ax.set_title(f'Price Trends (Last {hours}h)', fontsize=12, fontweight='bold')
        ax.set_ylabel('USD', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left', framealpha=0.9)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    def _plot_changes(self, ax, prices, period):
        """Plot price changes."""
        symbols = list(prices.keys())
        changes = [prices[sym].change_24h or 0 for sym in symbols]
        
        change_colors = [self.colors['positive'] if change >= 0 else self.colors['negative'] 
                        for change in changes]
        
        bars = ax.bar(symbols, changes, color=change_colors, alpha=0.8)
        ax.set_title(f'{period} Changes', fontsize=12, fontweight='bold')
        ax.set_ylabel('USD', fontsize=10)
        ax.axhline(y=0, color='white', linestyle='-', alpha=0.5)
        ax.grid(True, alpha=0.3)
        
        # Add value labels
        for bar, change in zip(bars, changes):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., 
                   height + (0.01 if height >= 0 else -0.01),
                   f'{change:+.2f}', ha='center', 
                   va='bottom' if height >= 0 else 'top', fontsize=9)
    
    def _plot_volume_indicator(self, ax):
        """Plot a mock volume indicator (placeholder)."""
        ax.set_title('Market Activity', fontsize=12, fontweight='bold')
        
        # Generate mock volume data
        hours = 12
        times = [datetime.now() - timedelta(hours=i) for i in range(hours, 0, -1)]
        volumes = [np.random.randint(50, 200) for _ in range(hours)]
        
        ax.bar(times, volumes, color=self.colors['grid'], alpha=0.6)
        ax.set_ylabel('Activity Index', fontsize=10)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        ax.grid(True, alpha=0.3)
    
    def _plot_news_preview(self, ax):
        """Plot news preview placeholder."""
        ax.set_title('Latest News', fontsize=12, fontweight='bold')
        ax.axis('off')
        
        # Mock news headlines
        headlines = [
            "Gold prices steady amid Fed uncertainty",
            "Silver demand rises in solar sector",
            "Platinum supply concerns persist",
            "Central banks continue gold purchases"
        ]
        
        y_pos = 0.9
        for headline in headlines[:3]:  # Show top 3
            ax.text(0.05, y_pos, f'• {headline[:25]}...', 
                   va='center', fontsize=8, wrap=True)
            y_pos -= 0.25
    
    def update_all_graphs(self) -> Dict[str, str]:
        """Update all graphs and return the file paths."""
        # Get current prices
        prices = self.market_data_fetcher.fetch_prices()
        
        if prices:
            # Update price history
            self.update_price_history(prices)
            
            # Generate all graphs
            graphs = {
                'current_prices': self.generate_current_prices_graph(prices),
                'price_history': self.generate_price_history_graph(),
                'market_overview': self.generate_market_overview()
            }
            
            logger.info(f"Updated all graphs: {list(graphs.keys())}")
            return graphs
        else:
            logger.warning("No price data available to update graphs")
            return {}
    
    def save_graph_metadata(self, graphs: Dict[str, str]):
        """Save metadata about generated graphs."""
        metadata = {
            'timestamp': self.get_current_utc_time().isoformat(),
            'graphs': graphs,
            'market_status': {m.name: self.is_market_open(m) for m in self.market_hours}
        }
        
        metadata_file = os.path.join(self.output_dir, 'graph_metadata.json')
        try:
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving graph metadata: {e}")

# Global instance
graph_generator = GraphGenerator()

def get_graph_generator() -> GraphGenerator:
    """Get the global graph generator instance."""
    return graph_generator
