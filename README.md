# Inwebstigate

**AI-Powered Web Investigation Tool**

An intelligent web investigation tool that uses AI to navigate the web, extract information, and answer your queries by intelligently browsing multiple websites.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Features

- **AI-Powered Navigation**: Uses LLMs to intelligently decide which links to follow
- **Smart Web Scraping**: Handles dynamic JavaScript-rendered content with Selenium
- **Visual Path Tracking**: See the investigation path and findings in real-time
- **Dual LLM Support**: Choose between local Ollama or cloud-based Groq API
- **Targeted Information Extraction**: AI extracts only relevant information for your query
- **Modern Web Interface**: Beautiful Flask web UI with real-time WebSocket updates
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Early Termination**: Automatically stops when sufficient information is found
- **Loop Detection**: Prevents getting stuck on the same URLs
- **Comprehensive Logging**: Detailed logs for debugging and monitoring

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Chrome browser (for Selenium)
- Ollama (if using local LLM) - [Install Ollama](https://ollama.ai)
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Installation

1. **Clone or navigate to the repository**:
```bash
cd /Users/nishchay.deep/Workspace/inwebstigate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**:
```bash
cp sample.env .env
```

Edit `.env` file with your settings:
```env
# Choose your LLM provider
LLM_PROVIDER=ollama

# For Ollama (local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# For Groq (cloud) - optional
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

4. **If using Ollama, make sure it's running**:
```bash
# In a separate terminal
ollama serve

# Pull your desired model
ollama pull llama3.2
```

### Running the Application

```bash
python3 main.py
```

Or:
```bash
python3 app.py
```

The application will automatically open in your default browser at `http://localhost:5000`

## Usage

1. **Enter your query**: Type the question or topic you want to investigate
2. **Optional - Set starting URL**: Provide a starting point, or leave blank to use DuckDuckGo
3. **Select LLM Provider**: Choose between Ollama (local) or Groq (cloud)
4. **Set max pages**: Limit how many pages to visit (default: 5)
5. **Start Investigation**: Click the button and watch the AI navigate!

### Example Queries

- "What are the latest features in Python 3.12?"
- "How does web scraping with Selenium work?"
- "What is the difference between Ollama and GPT?"
- "Find information about renewable energy trends in 2024"

## Architecture

```
inwebstigate/
├── main.py              # Application entry point
├── app.py               # Flask web application
├── agent.py             # AI navigation agent
├── scraper.py           # Web scraping with Selenium
├── llm_interface.py     # LLM abstraction (Ollama/Groq)
├── config.py            # Configuration management
├── templates/           # HTML templates
│   └── index.html       # Main web interface
├── static/              # Static assets
│   ├── css/style.css    # Styles
│   └── js/app.js        # Frontend JavaScript
├── requirements.txt     # Python dependencies
└── sample.env           # Environment template
```

## Configuration

### Available Ollama Models

You can use any model you have locally. Popular options:
- `llama3.2` - Fast and efficient
- `llama3.1` - More powerful
- `mistral` - Good alternative
- `mixtral` - High performance

To change the model, update your `.env`:
```env
OLLAMA_MODEL=your_model_name
```

Or select a different model and pull it:
```bash
ollama pull mistral
```

### Groq API Setup

1. Get API key from [Groq Console](https://console.groq.com)
2. Update `.env`:
```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_actual_api_key
```

### Optional: Bright Data Proxy

For advanced scraping with proxy support:
```env
BRIGHT_DATA_USERNAME=your_username
BRIGHT_DATA_PASSWORD=your_password
BRIGHT_DATA_HOST=proxy_host
BRIGHT_DATA_PORT=proxy_port
```

## Web Interface Features

### Navigation Log Tab
- Real-time updates of page visits via WebSocket
- Color-coded messages for easy reading
- Link selection reasoning displayed
- Auto-scrolling to latest updates

### Investigation Path Tab
- Table view of visited pages
- Key findings summary for each page
- Clickable URLs to sources
- Clear navigation flow

### Final Answer Tab
- Comprehensive answer to your query
- Source citations included
- Well-structured, formatted output
- Automatically switches when complete

## Troubleshooting

### "Cannot connect to Ollama"
Make sure Ollama is running:
```bash
ollama serve
```

### "Model not found"
Pull the model first:
```bash
ollama pull llama3.2
```

### Chrome/ChromeDriver issues
The app automatically downloads the correct ChromeDriver. If issues persist:
```bash
pip install --upgrade webdriver-manager
```

### Slow performance
- Use faster Ollama models (llama3.2 vs llama3.1)
- Reduce max pages setting
- Consider using Groq API for cloud speed

## Technologies Used

- **Flask**: Web framework for the backend
- **Selenium**: Browser automation and web scraping
- **BeautifulSoup4**: HTML parsing
- **Socket.IO**: Real-time WebSocket communication
- **Ollama**: Local LLM inference
- **Groq**: Cloud LLM API
- **WebDriver Manager**: Automatic ChromeDriver management

## Contributors

- **Nishchay Deep** 
- **Yash Pandey**

## Contributing


## License

MIT License - feel free to use this project for your own purposes!

## Acknowledgments



## Tips

- Start with specific queries for best results
- Provide a starting URL if you know a good source
- Use Groq for faster responses (requires API key)
- Monitor the Navigation Log to see AI's reasoning
- Adjust max pages based on query complexity
- The application will stop automatically when it finds sufficient information

---

**Happy Investigating!**

