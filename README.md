# Silver Ronin - 24/7 Precious Metals Livestream

A fully automated YouTube livestream that provides real-time precious metals market data, news, and analysis.

## Features

- Real-time precious metals price tracking
- Live market data visualization
- Automated news ticker with relevant updates
- Text-to-speech commentary
- 24/7 streaming capability
- Low-cost operation using free and open-source tools

## Setup

1. **Prerequisites**
   - Python 3.8+
   - OBS Studio
   - VPS (recommended) for 24/7 operation

2. **Installation**
   ```bash
   # Clone the repository
   git clone https://github.com/yourusername/silver-ronin.git
   cd silver-ronin
   
   # Create and activate a virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Configuration**
   - Copy `.env.example` to `.env`
   - Update the configuration with your API keys and settings

4. **Running the Stream**
   ```bash
   python src/main.py
   ```

## Project Structure

```
silveRonin/
├── config/               # Configuration files
├── src/                  # Source code
│   ├── data_fetchers/    # Market data and news fetchers
│   ├── graphics/         # Graph and visualization generation
│   ├── tts/              # Text-to-speech functionality
│   └── utils/            # Utility functions
├── assets/               # Static assets
│   ├── images/          # Images and overlays
│   └── music/           # Background music
├── logs/                 # Log files
├── .env.example         # Example environment variables
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## API Keys Required

- MetalpriceAPI or GoldAPI for precious metals prices
- (Optional) NewsData.io for enhanced news coverage

## License

MIT License
