"""
OBS Studio integration for Silver Ronin livestream.
Provides utilities for setting up and managing OBS scenes and sources.
"""
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from loguru import logger

class OBSIntegration:
    """OBS Studio integration helper for Silver Ronin."""
    
    def __init__(self):
        """Initialize OBS integration."""
        self.scene_collection = {
            "name": "Silver Ronin",
            "settings": {
                "output_format": "mkv",
                "video_format": "NV12",
                "audio_index": 1,
                "video_index": 0,
                "width": 1920,
                "height": 1080,
                "fps_num": 30,
                "fps_den": 1
            },
            "sources": [],
            "scenes": []
        }
        
        # Define scene layout
        self.setup_scenes()
    
    def setup_scenes(self):
        """Set up the scene configuration."""
        # Main streaming scene
        main_scene = {
            "name": "Main Stream",
            "uuid": "main-stream-scene",
            "settings": {},
            "sources": [
                # Background
                {
                    "name": "Background",
                    "type": "image_source",
                    "settings": {
                        "file": "assets/images/background.png",
                        "unload": False
                    },
                    "pos": {"x": 0, "y": 0},
                    "scale": {"x": 1.0, "y": 1.0}
                },
                # Market Overview Graph
                {
                    "name": "Market Overview",
                    "type": "image_source",
                    "settings": {
                        "file": "assets/images/market_overview.png",
                        "unload": False
                    },
                    "pos": {"x": 50, "y": 50},
                    "scale": {"x": 0.8, "y": 0.8}
                },
                # Price History Graph
                {
                    "name": "Price History",
                    "type": "image_source",
                    "settings": {
                        "file": "assets/images/price_history.png",
                        "unload": False
                    },
                    "pos": {"x": 960, "y": 50},
                    "scale": {"x": 0.45, "y": 0.45}
                },
                # News Ticker
                {
                    "name": "News Ticker",
                    "type": "text_source",
                    "settings": {
                        "text": "Loading latest news...",
                        "font": {"face": "Arial", "size": 24, "style": "regular"},
                        "color": 16777215,  # White
                        "background_color": 0,  # Transparent
                        "outline": False,
                        "drop_shadow": True,
                        "drop_shadow_color": 4278190080,  # Black shadow
                        "vertical": False,
                        "wrap": False,
                        "read_from_file": True,
                        "file": "assets/news_ticker.txt"
                    },
                    "pos": {"x": 0, "y": 950},
                    "scale": {"x": 1.0, "y": 1.0}
                },
                # Avatar Video
                {
                    "name": "Avatar",
                    "type": "image_source",
                    "settings": {
                        "file": "assets/images/avatar.png",
                        "unload": False
                    },
                    "pos": {"x": 1650, "y": 850},
                    "scale": {"x": 0.25, "y": 0.25}
                },
                # Audio Source (for TTS)
                {
                    "name": "TTS Audio",
                    "type": "ffmpeg_source",
                    "settings": {
                        "local_file": "assets/audio/latest_commentary.mp3",
                        "is_local_file": True,
                        "looping": False
                    },
                    "pos": {"x": 0, "y": 0},
                    "scale": {"x": 1.0, "y": 1.0}
                },
                # Background Music
                {
                    "name": "Background Music",
                    "type": "ffmpeg_source",
                    "settings": {
                        "local_file": "assets/music/background_playlist.mp3",
                        "is_local_file": True,
                        "looping": True
                    },
                    "pos": {"x": 0, "y": 0},
                    "scale": {"x": 1.0, "y": 1.0}
                }
            ]
        }
        
        self.scene_collection["scenes"] = [main_scene]
    
    def generate_scene_collection_file(self, filename: str = "silver_ronin_scene.json"):
        """Generate OBS scene collection file."""
        output_file = os.path.join("assets", filename)
        
        try:
            with open(output_file, 'w') as f:
                json.dump(self.scene_collection, f, indent=2)
            
            logger.info(f"Generated OBS scene collection: {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Error generating scene collection: {e}")
            return None
    
    def create_news_ticker_file(self, articles: List[Dict] = None):
        """Create news ticker text file for OBS."""
        ticker_file = os.path.join("assets", "news_ticker.txt")
        
        try:
            if articles:
                # Create scrolling ticker text
                ticker_text = "   ".join([f"• {article['title']}" for article in articles[:10]])
            else:
                ticker_text = "Welcome to Silver Ronin - 24/7 Precious Metals Market Coverage"
            
            with open(ticker_file, 'w', encoding='utf-8') as f:
                f.write(ticker_text)
            
            logger.info(f"Updated news ticker: {ticker_file}")
            return ticker_file
        except Exception as e:
            logger.error(f"Error creating news ticker: {e}")
            return None
    
    def create_background_image(self, filename: str = "background.png"):
        """Create a simple background image."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create 1920x1080 background
            img = Image.new('RGB', (1920, 1080), color='#1a1a1a')
            draw = ImageDraw.Draw(img)
            
            # Add gradient effect
            for y in range(1080):
                color_value = int(26 + (y / 1080) * 20)  # Dark gradient
                draw.line([(0, y), (1920, y)], fill=(color_value, color_value, color_value))
            
            # Add title
            try:
                font = ImageFont.truetype("arial.ttf", 60)
            except:
                font = ImageFont.load_default()
            
            text = "Silver Ronin"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (1920 - text_width) // 2
            y = 50
            
            # Add text shadow
            draw.text((x+2, y+2), text, fill=(0, 0, 0), font=font)
            draw.text((x, y), text, fill=(255, 215, 0), font=font)  # Gold color
            
            # Add subtitle
            subtitle = "24/7 Precious Metals Market Coverage"
            try:
                font_small = ImageFont.truetype("arial.ttf", 30)
            except:
                font_small = ImageFont.load_default()
            
            bbox = draw.textbbox((0, 0), subtitle, font=font_small)
            subtitle_width = bbox[2] - bbox[0]
            x = (1920 - subtitle_width) // 2
            y = 120
            
            draw.text((x+1, y+1), subtitle, fill=(0, 0, 0), font=font_small)
            draw.text((x, y), subtitle, fill=(192, 192, 192), font=font_small)
            
            # Save image
            output_path = os.path.join("assets", "images", filename)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            img.save(output_path)
            
            logger.info(f"Created background image: {output_path}")
            return output_path
            
        except ImportError:
            logger.warning("PIL not installed. Cannot create background image.")
            return None
        except Exception as e:
            logger.error(f"Error creating background image: {e}")
            return None
    
    def create_avatar_placeholder(self, filename: str = "avatar.png"):
        """Create a simple avatar placeholder."""
        try:
            from PIL import Image, ImageDraw
            
            # Create 400x400 avatar
            img = Image.new('RGBA', (400, 400), color=(0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Draw a simple robot/mascot
            # Head
            draw.ellipse([50, 50, 350, 350], fill=(255, 215, 0, 255), outline=(192, 192, 192, 255), width=3)
            
            # Eyes
            draw.ellipse([120, 120, 160, 160], fill=(0, 0, 0, 255))
            draw.ellipse([240, 120, 280, 160], fill=(0, 0, 0, 255))
            
            # Mouth
            draw.arc([150, 200, 250, 250], 0, 180, fill=(0, 0, 0, 255), width=3)
            
            # Antenna
            draw.line([200, 50, 200, 20], fill=(192, 192, 192, 255), width=5)
            draw.ellipse([190, 10, 210, 30], fill=(255, 0, 0, 255))
            
            # Save image
            output_path = os.path.join("assets", "images", filename)
            img.save(output_path)
            
            logger.info(f"Created avatar placeholder: {output_path}")
            return output_path
            
        except ImportError:
            logger.warning("PIL not installed. Cannot create avatar placeholder.")
            return None
        except Exception as e:
            logger.error(f"Error creating avatar placeholder: {e}")
            return None
    
    def setup_stream_settings(self, youtube_stream_key: str):
        """Generate OBS stream settings for YouTube."""
        settings = {
            "name": "YouTube Streaming",
            "type": "rtmp_custom",
            "settings": {
                "server": "rtmp://a.rtmp.youtube.com/live2",
                "key": youtube_stream_key,
                "use_auth": False,
                "bwtest": False
            }
        }
        
        settings_file = os.path.join("assets", "stream_settings.json")
        
        try:
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            
            logger.info(f"Generated stream settings: {settings_file}")
            return settings_file
        except Exception as e:
            logger.error(f"Error generating stream settings: {e}")
            return None
    
    def generate_setup_script(self):
        """Generate a script to help with OBS setup."""
        script = """@echo off
echo Silver Ronin OBS Setup Script
echo ============================
echo.

echo 1. Creating necessary directories...
if not exist "assets\\images" mkdir assets\\images
if not exist "assets\\audio" mkdir assets\\audio
if not exist "assets\\music" mkdir assets\\music
if not exist "logs" mkdir logs

echo.
echo 2. Creating placeholder assets...
python -c "from obs_integration import OBSIntegration; obs = OBSIntegration(); obs.create_background_image(); obs.create_avatar_placeholder()"

echo.
echo 3. Starting Silver Ronin application...
echo    (This will begin generating graphs and audio)
python src/main.py

echo.
echo Setup complete! Please configure OBS Studio manually:
echo   1. Import the scene collection from assets\\silver_ronin_scene.json
echo   2. Set up your YouTube stream key in OBS Settings > Stream
echo   3. Add the sources as specified in the scene collection
echo   4. Start streaming!
pause
"""
        
        script_file = os.path.join("setup_obs.bat")
        
        try:
            with open(script_file, 'w') as f:
                f.write(script)
            
            logger.info(f"Generated setup script: {script_file}")
            return script_file
        except Exception as e:
            logger.error(f"Error generating setup script: {e}")
            return None
    
    def update_obs_sources(self):
        """Update OBS source files with latest data."""
        try:
            # Update news ticker
            from src.data_fetchers.news_fetcher import get_news_fetcher
            news_fetcher = get_news_fetcher()
            articles = news_fetcher.fetch_news(max_articles=10)
            
            if articles:
                self.create_news_ticker_file([article.to_dict() for article in articles])
            
            logger.info("Updated OBS source files")
            return True
        except Exception as e:
            logger.error(f"Error updating OBS sources: {e}")
            return False

def main():
    """Main function to set up OBS integration."""
    obs = OBSIntegration()
    
    print("Setting up OBS integration for Silver Ronin...")
    
    # Generate all files
    obs.generate_scene_collection_file()
    obs.create_background_image()
    obs.create_avatar_placeholder()
    obs.create_news_ticker_file()
    obs.generate_setup_script()
    
    # Get YouTube stream key from environment
    stream_key = os.getenv('YOUTUBE_STREAM_KEY')
    if stream_key:
        obs.setup_stream_settings(stream_key)
    else:
        print("Warning: YOUTUBE_STREAM_KEY not found in environment variables")
    
    print("\nOBS integration setup complete!")
    print("Files generated in assets/ directory")
    print("\nNext steps:")
    print("1. Open OBS Studio")
    print("2. Import scene collection from assets/silver_ronin_scene.json")
    print("3. Configure your YouTube stream key")
    print("4. Add background music to assets/music/")
    print("5. Start the Silver Ronin application: python src/main.py")

if __name__ == "__main__":
    main()
