#!/usr/bin/env python3
"""
Silver Ronin - 24/7 Precious Metals Livestream
Main application entry point.
"""
import os
import logging
import time
from datetime import datetime
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger.add(
    os.path.join(os.getenv('LOGS_DIR', 'logs'), 'silver_ronin.log'),
    rotation='1 day',
    retention='7 days',
    level=os.getenv('LOG_LEVEL', 'INFO')
)

class SilverRonin:
    """Main application class for Silver Ronin livestream."""
    
    def __init__(self):
        """Initialize the application."""
        self.running = False
        self.update_interval = int(os.getenv('UPDATE_INTERVAL', '60'))
        
        # Import components
        from .data_fetchers import get_market_data_fetcher, get_news_fetcher
        from .graphics import get_graph_generator
        from .tts import get_tts_engine
        
        # Initialize components
        self.market_data_fetcher = get_market_data_fetcher()
        self.news_fetcher = get_news_fetcher()
        self.graph_generator = get_graph_generator()
        self.tts_engine = get_tts_engine()
        
        logger.info("Silver Ronin initialized")
    
    def setup(self):
        """Set up the application components."""
        try:
            logger.info("Setting up application components...")
            
            # Create necessary directories
            os.makedirs("assets/images", exist_ok=True)
            os.makedirs("assets/audio", exist_ok=True)
            os.makedirs("logs", exist_ok=True)
            
            # Test connections
            logger.info("Testing market data connection...")
            prices = self.market_data_fetcher.fetch_prices()
            if prices:
                logger.info(f"✓ Market data connected: {len(prices)} metals")
            else:
                logger.warning("⚠ Market data connection failed")
            
            logger.info("Testing news fetcher...")
            articles = self.news_fetcher.fetch_news(max_articles=3)
            if articles:
                logger.info(f"✓ News fetcher working: {len(articles)} articles")
            else:
                logger.warning("⚠ News fetcher returned no articles")
            
            return True
        except Exception as e:
            logger.error(f"Failed to set up application: {e}")
            return False
    
    def update(self):
        """Update all components."""
        try:
            logger.debug("Updating components...")
            
            # Update market data
            prices = self.market_data_fetcher.fetch_prices()
            if prices:
                logger.debug(f"Updated prices: {list(prices.keys())}")
            
            # Update news
            articles = self.news_fetcher.fetch_news(max_articles=10)
            if articles:
                logger.debug(f"Updated news: {len(articles)} articles")
            
            # Update graphs
            graphs = self.graph_generator.update_all_graphs()
            if graphs:
                logger.debug(f"Updated graphs: {list(graphs.keys())}")
            
            # Update TTS
            tts_status = self.tts_engine.update_all()
            if tts_status['audio_files_generated'] > 0:
                logger.info(f"Generated {tts_status['audio_files_generated']} audio files")
            
            return True
        except Exception as e:
            logger.error(f"Update failed: {e}")
            return False
    
    def run(self):
        """Run the main application loop."""
        if not self.setup():
            logger.error("Failed to set up application. Exiting...")
            return
        
        self.running = True
        logger.info("Starting Silver Ronin livestream...")
        
        try:
            while self.running:
                start_time = time.time()
                
                # Update all components
                if not self.update():
                    logger.warning("Update cycle had errors")
                
                # Calculate sleep time to maintain update interval
                elapsed = time.time() - start_time
                sleep_time = max(1, self.update_interval - elapsed)
                
                logger.debug(f"Update completed in {elapsed:.2f}s. Sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            logger.info("Shutting down gracefully...")
        except Exception as e:
            logger.critical(f"Unexpected error: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Clean up resources and shut down the application."""
        logger.info("Shutting down...")
        self.running = False

if __name__ == "__main__":
    app = SilverRonin()
    app.run()
