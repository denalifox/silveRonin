# Silver Ronin - Setup Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Get API Keys
- **MetalPriceAPI**: Get a free API key from https://metalpriceapi.com/
- Create a `.env` file in the project root:
  ```
  METALPRICE_API_KEY=your_api_key_here
  ```

### 3. Test the Components
```bash
# Test market data fetcher
python test_market_data.py

# Test news fetcher
python test_news_fetcher.py
```

## GitHub Setup

### 1. Create GitHub Repository
1. Go to https://github.com/new
2. Repository name: `silveRonin`
3. Don't initialize with README (we already have one)
4. Click "Create repository"

### 2. Connect Local Repository
```bash
# Replace YOUR_USERNAME with your GitHub username
git remote add origin https://github.com/YOUR_USERNAME/silveRonin.git
git branch -M main
git push -u origin main
```

## VPS Setup (for 24/7 Streaming)

### Option 1: Oracle Cloud Free Tier (Recommended)
1. Sign up at https://oracle.com/cloud/free
2. Create an ARM-based instance with Ubuntu
3. Specs: Up to 4 OCPUs, 24GB RAM, 200GB storage

### Option 2: Low-Cost Paid VPS
- DigitalOcean: $6/month droplet
- Vultr: $5/month instance

### VPS Installation Commands
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install desktop environment (for OBS)
sudo apt install ubuntu-desktop -y

# Install OBS Studio
sudo apt install obs-studio -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv -y

# Clone your repository
git clone https://github.com/YOUR_USERNAME/silveRonin.git
cd silveRonin

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your API keys
```

## Next Steps

1. **Test locally first** - Make sure everything works on your computer
2. **Set up GitHub** - Push your code to GitHub for version control
3. **Get API keys** - Sign up for MetalPriceAPI
4. **Set up VPS** - Choose a VPS provider and set up the environment
5. **Install OBS** - Configure OBS for streaming
6. **Create YouTube stream** - Get your YouTube stream key

## Testing Checklist

- [ ] Market data fetcher works
- [ ] News fetcher works
- [ ] Graph generation works (when implemented)
- [ ] TTS works (when implemented)
- [ ] OBS configuration complete
- [ ] YouTube stream key configured

## Troubleshooting

### Common Issues
1. **API Key Errors**: Make sure your API key is correctly set in `.env`
2. **Network Issues**: Check firewall settings and internet connection
3. **Python Dependencies**: Make sure all packages are installed correctly

### Getting Help
- Check the logs in the `logs/` directory
- Run test scripts individually to isolate issues
- Check GitHub issues for common problems
