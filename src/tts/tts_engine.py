"""
Text-to-speech engine for generating avatar commentary.
Supports multiple TTS backends and voice customization.
"""
import os
import time
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from loguru import logger
import json
import random

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    logger.warning("gTTS not available. Install with: pip install gTTS")

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    logger.warning("pyttsx3 not available. Install with: pip install pyttsx3")

from ..data_fetchers.market_data import MetalPrice, get_market_data_fetcher
from ..data_fetchers.news_fetcher import NewsArticle, get_news_fetcher

@dataclass
class CommentaryItem:
    """Data class for commentary items."""
    text: str
    priority: int  # 1=high, 2=medium, 3=low
    category: str  # 'market', 'news', 'analysis'
    timestamp: datetime
    audio_file: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'text': self.text,
            'priority': self.priority,
            'category': self.category,
            'timestamp': self.timestamp.isoformat(),
            'audio_file': self.audio_file
        }

class TTSEngine:
    """Text-to-speech engine for generating avatar commentary."""
    
    def __init__(self, output_dir: str = "assets/audio"):
        """Initialize the TTS engine.
        
        Args:
            output_dir: Directory to save generated audio files
        """
        self.output_dir = output_dir
        self.market_data_fetcher = get_market_data_fetcher()
        self.news_fetcher = get_news_fetcher()
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize TTS engines
        self.engines = {}
        self._init_engines()
        
        # Commentary queue
        self.commentary_queue: List[CommentaryItem] = []
        self.max_queue_size = 50
        
        # Voice settings
        self.voice_settings = {
            'gtts': {
                'lang': 'en',
                'slow': False,
                'tld': 'us'  # US English accent
            },
            'pyttsx3': {
                'rate': 150,  # Words per minute
                'volume': 0.9
            }
        }
        
        # Commentary templates
        self.templates = {
            'price_movement': [
                "Breaking: {metal} is now trading at ${price:.2f}, {change_direction} by ${abs_change):.2f} today.",
                "Market update: {metal} prices {change_direction} to ${price:.2f}, showing {change_direction} momentum.",
                "Precious metals alert: {metal} at ${price:.2f}, {change_direction} by {change_pct:.1f}% in the last 24 hours."
            ],
            'market_status': [
                "Markets are currently {status} with {open_markets} trading actively.",
                "Global market overview: {open_markets} are open, {closed_markets} are closed.",
                "Trading activity: {open_markets} sessions are currently active worldwide."
            ],
            'news_headline': [
                "Latest development: {headline}",
                "Breaking news from {source}: {headline}",
                "Market-moving news: {headline}"
            ],
            'analysis': [
                "Technical analysis suggests {metal} is showing {trend} patterns.",
                "Market sentiment for {metal} appears {sentiment} based on recent price action.",
                "Looking at the charts, {metal} is demonstrating {pattern} behavior."
            ]
        }
        
        # Last commentary times (to avoid repetition)
        self.last_commentary = {
            'price_update': 0,
            'news_update': 0,
            'market_status': 0
        }
        
        # Cooldown periods (seconds)
        self.cooldowns = {
            'price_update': 300,  # 5 minutes
            'news_update': 600,   # 10 minutes
            'market_status': 1800  # 30 minutes
        }
    
    def _init_engines(self):
        """Initialize available TTS engines."""
        if GTTS_AVAILABLE:
            self.engines['gtts'] = gTTS
            logger.info("Initialized gTTS engine")
        
        if PYTTSX3_AVAILABLE:
            try:
                self.engines['pyttsx3'] = pyttsx3.init()
                logger.info("Initialized pyttsx3 engine")
            except Exception as e:
                logger.error(f"Failed to initialize pyttsx3: {e}")
        
        if not self.engines:
            logger.error("No TTS engines available. Please install gTTS or pyttsx3")
    
    def generate_audio(self, text: str, engine: str = 'gtts', filename: str = None) -> Optional[str]:
        """Generate audio from text using specified engine.
        
        Args:
            text: Text to convert to speech
            engine: TTS engine to use ('gtts' or 'pyttsx3')
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to generated audio file, or None if failed
        """
        if engine not in self.engines:
            logger.error(f"TTS engine '{engine}' not available")
            return None
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"commentary_{timestamp}_{hash(text) % 10000}.mp3"
        
        output_path = os.path.join(self.output_dir, filename)
        
        try:
            if engine == 'gtts':
                return self._generate_gtts(text, output_path)
            elif engine == 'pyttsx3':
                return self._generate_pyttsx3(text, output_path)
        except Exception as e:
            logger.error(f"Error generating audio with {engine}: {e}")
            return None
    
    def _generate_gtts(self, text: str, output_path: str) -> Optional[str]:
        """Generate audio using gTTS."""
        try:
            tts = gTTS(
                text=text,
                lang=self.voice_settings['gtts']['lang'],
                slow=self.voice_settings['gtts']['slow'],
                tld=self.voice_settings['gtts']['tld']
            )
            tts.save(output_path)
            logger.debug(f"Generated gTTS audio: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"gTTS generation failed: {e}")
            return None
    
    def _generate_pyttsx3(self, text: str, output_path: str) -> Optional[str]:
        """Generate audio using pyttsx3."""
        try:
            engine = self.engines['pyttsx3']
            
            # Set voice properties
            engine.setProperty('rate', self.voice_settings['pyttsx3']['rate'])
            engine.setProperty('volume', self.voice_settings['pyttsx3']['volume'])
            
            # Save to file
            engine.save_to_file(text, output_path)
            engine.runAndWait()
            
            logger.debug(f"Generated pyttsx3 audio: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"pyttsx3 generation failed: {e}")
            return None
    
    def generate_price_commentary(self, prices: Dict[str, MetalPrice]) -> List[CommentaryItem]:
        """Generate commentary based on current prices."""
        commentary = []
        current_time = datetime.now()
        
        # Check cooldown
        if (current_time.timestamp() - self.last_commentary['price_update']) < self.cooldowns['price_update']:
            return commentary
        
        for symbol, price in prices.items():
            # Only comment on significant movements
            if price.change_pct_24h and abs(price.change_pct_24h) > 0.5:  # 0.5% threshold
                change_direction = "up" if price.change_24h > 0 else "down"
                
                # Select random template
                template = random.choice(self.templates['price_movement'])
                
                text = template.format(
                    metal=price.name,
                    price=price.price,
                    change_direction=change_direction,
                    abs_change=abs(price.change_24h),
                    change_pct=price.change_pct_24h
                )
                
                item = CommentaryItem(
                    text=text,
                    priority=1 if abs(price.change_pct_24h) > 2 else 2,
                    category='market',
                    timestamp=current_time
                )
                
                commentary.append(item)
        
        if commentary:
            self.last_commentary['price_update'] = current_time.timestamp()
        
        return commentary
    
    def generate_news_commentary(self, articles: List[NewsArticle]) -> List[CommentaryItem]:
        """Generate commentary based on news articles."""
        commentary = []
        current_time = datetime.now()
        
        # Check cooldown
        if (current_time.timestamp() - self.last_commentary['news_update']) < self.cooldowns['news_update']:
            return commentary
        
        # Take top 3 most recent articles
        for article in articles[:3]:
            template = random.choice(self.templates['news_headline'])
            
            text = template.format(
                headline=article.title,
                source=article.source
            )
            
            item = CommentaryItem(
                text=text,
                priority=1,
                category='news',
                timestamp=current_time
            )
            
            commentary.append(item)
        
        if commentary:
            self.last_commentary['news_update'] = current_time.timestamp()
        
        return commentary
    
    def generate_market_status_commentary(self) -> List[CommentaryItem]:
        """Generate commentary based on market status."""
        commentary = []
        current_time = datetime.now()
        
        # Check cooldown
        if (current_time.timestamp() - self.last_commentary['market_status']) < self.cooldowns['market_status']:
            return commentary
        
        # Check which markets are open
        from ..graphics.graph_generator import GraphGenerator
        graph_gen = GraphGenerator()
        
        open_markets = [m.name for m in graph_gen.market_hours if graph_gen.is_market_open(m)]
        closed_markets = [m.name for m in graph_gen.market_hours if not graph_gen.is_market_open(m)]
        
        status = "active" if open_markets else "quiet"
        
        template = random.choice(self.templates['market_status'])
        text = template.format(
            status=status,
            open_markets=", ".join(open_markets) if open_markets else "no major markets",
            closed_markets=", ".join(closed_markets) if closed_markets else "all markets"
        )
        
        item = CommentaryItem(
            text=text,
            priority=2,
            category='market',
            timestamp=current_time
        )
        
        commentary.append(item)
        self.last_commentary['market_status'] = current_time.timestamp()
        
        return commentary
    
    def generate_analysis_commentary(self, prices: Dict[str, MetalPrice]) -> List[CommentaryItem]:
        """Generate technical analysis commentary."""
        commentary = []
        current_time = datetime.now()
        
        # Simple analysis based on price movements
        for symbol, price in prices.items():
            if price.change_24h is None:
                continue
            
            # Determine trend
            if price.change_24h > 1:
                trend = "strong upward"
                sentiment = "bullish"
                pattern = "breakout"
            elif price.change_24h > 0:
                trend = "moderate upward"
                sentiment = "optimistic"
                pattern = "accumulation"
            elif price.change_24h < -1:
                trend = "strong downward"
                sentiment = "bearish"
                pattern = "distribution"
            else:
                trend = "sideways"
                sentiment = "neutral"
                pattern = "consolidation"
            
            template = random.choice(self.templates['analysis'])
            text = template.format(
                metal=price.name,
                trend=trend,
                sentiment=sentiment,
                pattern=pattern
            )
            
            item = CommentaryItem(
                text=text,
                priority=3,
                category='analysis',
                timestamp=current_time
            )
            
            commentary.append(item)
        
        return commentary
    
    def update_commentary_queue(self) -> List[CommentaryItem]:
        """Update the commentary queue with new items."""
        # Get current data
        prices = self.market_data_fetcher.fetch_prices()
        articles = self.news_fetcher.fetch_news(max_articles=5)
        
        # Generate commentary
        new_commentary = []
        
        if prices:
            new_commentary.extend(self.generate_price_commentary(prices))
            new_commentary.extend(self.generate_analysis_commentary(prices))
        
        new_commentary.extend(self.generate_news_commentary(articles))
        new_commentary.extend(self.generate_market_status_commentary())
        
        # Add to queue
        for item in new_commentary:
            self.commentary_queue.append(item)
        
        # Sort by priority and timestamp
        self.commentary_queue.sort(key=lambda x: (x.priority, x.timestamp))
        
        # Limit queue size
        if len(self.commentary_queue) > self.max_queue_size:
            self.commentary_queue = self.commentary_queue[-self.max_queue_size:]
        
        return new_commentary
    
    def generate_audio_for_queue(self, max_items: int = 5) -> List[str]:
        """Generate audio files for items in the queue."""
        generated_files = []
        
        # Take top items by priority
        items_to_process = self.commentary_queue[:max_items]
        
        for item in items_to_process:
            if not item.audio_file or not os.path.exists(item.audio_file):
                # Generate audio
                engine = 'gtts' if 'gtts' in self.engines else 'pyttsx3'
                audio_file = self.generate_audio(item.text, engine=engine)
                
                if audio_file:
                    item.audio_file = audio_file
                    generated_files.append(audio_file)
                    logger.info(f"Generated audio: {item.text[:50]}...")
                else:
                    logger.warning(f"Failed to generate audio for: {item.text[:50]}...")
        
        return generated_files
    
    def get_next_commentary(self) -> Optional[CommentaryItem]:
        """Get the next commentary item from the queue."""
        if not self.commentary_queue:
            return None
        
        # Remove and return the first item
        return self.commentary_queue.pop(0)
    
    def save_commentary_log(self, filename: str = None):
        """Save commentary log to file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d")
            filename = f"commentary_log_{timestamp}.json"
        
        log_file = os.path.join(self.output_dir, filename)
        
        try:
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'queue': [item.to_dict() for item in self.commentary_queue],
                'last_commentary': self.last_commentary
            }
            
            with open(log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            logger.info(f"Saved commentary log: {log_file}")
        except Exception as e:
            logger.error(f"Error saving commentary log: {e}")
    
    def update_all(self) -> Dict[str, any]:
        """Update all TTS components and return status."""
        # Update commentary queue
        new_items = self.update_commentary_queue()
        
        # Generate audio for queue
        audio_files = self.generate_audio_for_queue()
        
        # Save log
        self.save_commentary_log()
        
        return {
            'new_commentary_items': len(new_items),
            'queue_size': len(self.commentary_queue),
            'audio_files_generated': len(audio_files),
            'audio_files': audio_files
        }

# Global instance
tts_engine = TTSEngine()

def get_tts_engine() -> TTSEngine:
    """Get the global TTS engine instance."""
    return tts_engine
