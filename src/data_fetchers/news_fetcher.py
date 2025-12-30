"""
News fetcher for precious metals related news.
Supports multiple RSS feeds and news sources with filtering and caching.
"""
import os
import feedparser
import requests
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.parse import urlparse
from loguru import logger
import time
import random
import json

@dataclass
class NewsArticle:
    """Data class for storing news article information."""
    title: str
    url: str
    source: str
    published: datetime
    summary: str = ""
    image_url: Optional[str] = None
    category: str = "general"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'title': self.title,
            'url': self.url,
            'source': self.source,
            'published': self.published.isoformat(),
            'summary': self.summary,
            'image_url': self.image_url,
            'category': self.category
        }
    
    @property
    def formatted_date(self) -> str:
        """Format the published date in a human-readable format."""
        now = datetime.now(self.published.tzinfo) if self.published.tzinfo else datetime.now()
        delta = now - self.published
        
        if delta < timedelta(minutes=1):
            return "Just now"
        elif delta < timedelta(hours=1):
            minutes = int(delta.seconds / 60)
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        elif delta < timedelta(days=1):
            hours = int(delta.seconds / 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif delta < timedelta(days=30):
            days = delta.days
            return f"{days} day{'s' if days > 1 else ''} ago"
        else:
            return self.published.strftime("%b %d, %Y")

class NewsFetcher:
    """Fetches news articles related to precious metals from various sources."""
    
    def __init__(self, cache_ttl: int = 300):
        """Initialize the news fetcher.
        
        Args:
            cache_ttl: Time in seconds to cache news articles
        """
        self.cache_ttl = cache_ttl
        self.last_fetch_time = 0
        self.cached_articles = []
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        ]
        
        # Define news sources with their RSS feeds
        self.sources = {
            'kitco': {
                'url': 'https://www.kitco.com/rss/kitco-news.xml',
                'type': 'rss',
                'category': 'precious-metals'
            },
            'mining': {
                'url': 'https://www.mining.com/feed/',
                'type': 'rss',
                'category': 'mining'
            },
            'reuters': {
                'url': 'https://www.reuters.com/tags/precious-metals/feed/',
                'type': 'rss',
                'category': 'precious-metals'
            }
        }
        
        # Keywords to filter relevant articles
        self.keywords = [
            'gold', 'silver', 'platinum', 'palladium', 'precious metals',
            'bullion', 'mining', 'commodities', 'inflation', 'fed', 'interest rates',
            'central bank', 'xau', 'xag', 'xpt', 'xpd', 'kitco', 'comex', 'lbma'
        ]
    
    def _get_random_headers(self) -> dict:
        """Get random headers to avoid being blocked."""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
    
    def _parse_rss_feed(self, url: str, source: str, category: str) -> List[NewsArticle]:
        """Parse an RSS feed and return a list of NewsArticle objects."""
        articles = []
        try:
            # Add cache-busting parameter to avoid cached responses
            cache_buster = int(time.time())
            feed_url = f"{url}?{cache_buster}" if "?" not in url else f"{url}&{cache_buster}"
            
            # Parse the feed with a timeout
            feed = feedparser.parse(feed_url, request_headers=self._get_random_headers(), 
                                  timeout=10)
            
            for entry in feed.entries:
                try:
                    # Skip entries without a title or URL
                    if not getattr(entry, 'title', None) or not getattr(entry, 'link', None):
                        continue
                    
                    # Parse the published date
                    published = datetime.now()
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        published = datetime(*entry.updated_parsed[:6])
                    
                    # Skip articles older than 7 days
                    if (datetime.now() - published) > timedelta(days=7):
                        continue
                    
                    # Create the article
                    article = NewsArticle(
                        title=entry.title,
                        url=entry.link,
                        source=source.capitalize(),
                        published=published,
                        summary=getattr(entry, 'summary', '')[:200] + '...',
                        category=category
                    )
                    
                    # Try to get an image URL if available
                    if hasattr(entry, 'media_content') and entry.media_content:
                        article.image_url = entry.media_content[0]['url']
                    elif hasattr(entry, 'links') and entry.links:
                        for link in entry.links:
                            if link.get('type', '').startswith('image/'):
                                article.image_url = link.href
                                break
                    
                    articles.append(article)
                    
                except Exception as e:
                    logger.warning(f"Error parsing article from {source}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error fetching RSS feed {url}: {e}")
        
        return articles
    
    def _filter_relevant_articles(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Filter articles based on relevance to precious metals."""
        relevant_articles = []
        
        for article in articles:
            # Check if any keyword is in the title or summary (case-insensitive)
            content = f"{article.title} {article.summary}".lower()
            if any(keyword.lower() in content for keyword in self.keywords):
                relevant_articles.append(article)
        
        return relevant_articles
    
    def _remove_duplicates(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Remove duplicate articles based on URL and title similarity."""
        seen_urls = set()
        unique_articles = []
        
        for article in sorted(articles, key=lambda x: x.published, reverse=True):
            # Normalize URL
            url = article.url.lower().split('?')[0]  # Remove query parameters
            url = url.rstrip('/')  # Remove trailing slashes
            
            # Check if we've seen this URL before
            if url in seen_urls:
                continue
                
            # Check for similar titles (prevent different URLs with same content)
            title = article.title.lower()
            is_duplicate = False
            for seen_title in [a.title.lower() for a in unique_articles]:
                # If titles are very similar, consider them duplicates
                if self._similar(title, seen_title) > 0.8:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_urls.add(url)
                unique_articles.append(article)
        
        return unique_articles
    
    def _similar(self, a: str, b: str) -> float:
        """Calculate similarity ratio between two strings."""
        from difflib import SequenceMatcher
        return SequenceMatcher(None, a, b).ratio()
    
    def fetch_news(self, max_articles: int = 20) -> List[NewsArticle]:
        """Fetch news articles from all sources.
        
        Args:
            max_articles: Maximum number of articles to return
            
        Returns:
            List of NewsArticle objects, sorted by date (newest first)
        """
        # Check cache first
        current_time = time.time()
        if (current_time - self.last_fetch_time) < self.cache_ttl and self.cached_articles:
            logger.debug("Returning cached news articles")
            return self.cached_articles[:max_articles]
        
        all_articles = []
        
        # Fetch from each source
        for source_name, source_info in self.sources.items():
            try:
                logger.debug(f"Fetching news from {source_name}...")
                
                if source_info['type'] == 'rss':
                    articles = self._parse_rss_feed(
                        source_info['url'], 
                        source_name,
                        source_info.get('category', 'general')
                    )
                else:
                    continue
                
                all_articles.extend(articles)
                logger.debug(f"Found {len(articles)} articles from {source_name}")
                
                # Be nice to the servers
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error fetching from {source_name}: {e}")
                continue
        
        # Process the articles
        relevant_articles = self._filter_relevant_articles(all_articles)
        unique_articles = self._remove_duplicates(relevant_articles)
        
        # Sort by date (newest first)
        unique_articles.sort(key=lambda x: x.published, reverse=True)
        
        # Update cache
        self.cached_articles = unique_articles
        self.last_fetch_time = current_time
        
        return unique_articles[:max_articles]
    
    def save_to_json(self, articles: List[NewsArticle], filename: str) -> None:
        """Save articles to a JSON file.
        
        Args:
            articles: List of NewsArticle objects
            filename: Output JSON filename
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump([article.to_dict() for article in articles], f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(articles)} articles to {filename}")
        except Exception as e:
            logger.error(f"Error saving articles to {filename}: {e}")

# Global instance
news_fetcher = NewsFetcher()

def get_news_fetcher() -> NewsFetcher:
    """Get the global news fetcher instance."""
    return news_fetcher
