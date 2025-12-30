#!/usr/bin/env python3
"""Test script for the news fetcher."""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from src.data_fetchers.news_fetcher import get_news_fetcher

def main():
    # Load environment variables
    load_dotenv()
    
    # Get the fetcher
    fetcher = get_news_fetcher()
    
    print("Fetching precious metals news...")
    try:
        articles = fetcher.fetch_news(max_articles=10)
        
        if not articles:
            print("No articles found. Check your internet connection and try again.")
            return
        
        print(f"\nFound {len(articles)} articles:\n")
        for i, article in enumerate(articles, 1):
            print(f"{i}. {article.title}")
            print(f"   Source: {article.source}")
            print(f"   Published: {article.formatted_date}")
            print(f"   URL: {article.url}")
            if article.summary:
                print(f"   Summary: {article.summary}")
            print()
        
        # Save to file for reference
        fetcher.save_to_json(articles, "latest_news.json")
        print(f"\nSaved articles to latest_news.json")
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
