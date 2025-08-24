# Ollama Flask Chatbot

A simple Flask web application that provides a chat interface for Ollama AI models with Wiki.js API integration.

## Features

- Web-based chat interface with syntax highlighting for code
- Support for both Ollama CLI and HTTP API
- **Wiki.js API integration** for accessing structured content
- Health check endpoints for monitoring
- Test page for troubleshooting
- Windows-compatible with proper encoding handling
- URL content fetching and analysis

## Prerequisites

1. **Python 3.7+** installed on your system
2. **Ollama** installed and running (download from https://ollama.ai/)
3. **Wiki.js server** running (optional, for enhanced content access)

## Installation

1. **Clone or download this repository**

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install and start Ollama:**
   - Download from https://ollama.ai/
   - Install and start the Ollama service
   - Pull a model (e.g., `ollama pull llama3.1:latest`)

4. **Configure Wiki.js API (optional):**
   - The application includes a pre-configured API key for Wiki.js
   - Edit `WIKIJS_BASE_URL` and `WIKIJS_API_KEY` in `botv2.py` if needed

## Usage

1. **Start the Flask application:**
   ```bash
   python botv2.py
   ```

2. **Access the application:**
   - Main chat interface: http://localhost:5000
   - Test page: http://localhost:5000/test

3. **Test connections:**
   - Visit http://localhost:5000/test to check all connections
   - Test Ollama, Wiki.js connectivity, and API functionality

## Configuration

### Model Selection

Edit the `OLLAMA_MODEL` variable in `botv2.py` to use a different model:

```python
OLLAMA_MODEL = 'llama3.1:latest'  # Change to your preferred model
```

### Wiki.js Configuration

The application includes Wiki.js API integration. You can modify these settings in `botv2.py`:

```python
WIKIJS_BASE_URL = 'http://192.168.5.66:3000'
WIKIJS_API_KEY = 'your-api-key-here'
```

### Available Models

To see available models, visit http://localhost:5000/test or run:
```bash
ollama list
```

## API Endpoints

- `GET /` - Main chat interface
- `GET /test` - Test and troubleshooting page
- `POST /ask` - Send a prompt to the AI
- `GET /health` - Health check endpoint
- `GET /models` - List available Ollama models
- `POST /test-simple` - Simple test endpoint
- `GET /test-wiki` - Test Wiki.js connectivity
- `GET /test-wiki-api` - Test Wiki.js API functionality
- `GET /wiki-pages` - List all Wiki.js pages
- `POST /fetch-url` - Fetch content from any URL

## Chat Features

### URL Content Analysis

The chatbot can automatically detect URLs in prompts and fetch content:

- **Wiki.js URLs**: Uses the API for structured content access
- **Other URLs**: Scrapes and extracts meaningful text content
- **Content Processing**: Converts HTML to clean text for AI analysis

### Example Prompts

- *"Can you access content from http://192.168.5.66:3000/"*
- *"What pages are available on the Wiki.js server?"*
- *"Summarize the content from http://example.com"*

## Troubleshooting

### Common Issues

1. **"Ollama not found" error:**
   - Make sure Ollama is installed from https://ollama.ai/
   - Add Ollama to your system PATH

2. **"Cannot connect to Ollama" error:**
   - Start Ollama service: `ollama serve`
   - Check if port 11434 is accessible
   - Verify firewall settings

3. **"Model not found" error:**
   - Pull the model first: `ollama pull [model-name]`
   - Check available models: `ollama list`

4. **"Wiki.js API error":**
   - Verify the API key is correct
   - Check if Wiki.js is running and accessible
   - Ensure the API endpoints are enabled

5. **Unicode/encoding errors (Windows):**
   - The application now handles Windows encoding issues automatically
   - If problems persist, try running as administrator

6. **Timeout errors:**
   - Increase timeout values in the code if needed
   - Check your system's performance and available memory

### Windows-Specific Notes

- The application uses `CREATE_NO_WINDOW` flag to hide console windows
- UTF-8 encoding with error replacement is used for subprocess calls
- Windows-specific error handling is implemented

### Testing

Use the test page at http://localhost:5000/test to:
- Check if Ollama is running
- List available models
- Test Wiki.js connectivity and API
- Test simple prompts
- Get troubleshooting guidance

## Development

### Project Structure

```
CodeReview/
├── botv2.py              # Main Flask application
├── requirements.txt      # Python dependencies
├── README.md            # This file
└── templates/
    ├── index.html       # Main chat interface
    └── test.html        # Test and troubleshooting page
```

### Adding Features

- The application is modular and easy to extend
- Add new routes in `botv2.py`
- Modify templates in the `templates/` directory
- Update `requirements.txt` for new dependencies

## License

This project is open source and available under the MIT License. 