# AI Chat Application

A Flask-based web application that provides a chat interface to interact with Ollama AI models. The application features a modern web UI with syntax highlighting for code blocks and inline code formatting.

## Features

- 🤖 Chat interface with Ollama AI models
- 💻 Syntax highlighting for code blocks
- 📋 Copy-to-clipboard functionality for code
- 🎨 Modern, responsive web interface
- 🔄 Real-time chat experience
- 🛠️ Two deployment options (local and network-accessible)

## Prerequisites

Before running this application, you need to have the following installed:

### 1. Python
- Python 3.7 or higher
- Download from [python.org](https://www.python.org/downloads/)
- **Important**: Make sure to check "Add Python to PATH" during installation

### 2. Ollama
- Install Ollama from [ollama.ai](https://ollama.ai/)
- After installation, pull the required model:
  ```bash
  ollama pull llama3.1:latest
  ```
- Start the Ollama service:
  ```bash
  ollama serve
  ```

## Installation

1. **Clone or download this repository**
   ```bash
   git clone <repository-url>
   cd CodeReview
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   Or install manually:
   ```bash
   pip install flask requests
   ```

## Running the Application

### Option 1: Local Access Only (app.py)
```bash
python app.py
```
- **Access URL**: http://localhost:5000
- **Best for**: Development and local testing

### Option 2: Network Access (botv2.py)
```bash
python botv2.py
```
- **Access URL**: http://localhost:5000 (local) or http://your-ip:5000 (network)
- **Best for**: Sharing with other devices on your network

## Usage

1. **Ensure Ollama is running**
   - Make sure Ollama service is started: `ollama serve`
   - Verify the model is available: `ollama list`

2. **Start the Flask application**
   - Run one of the Python files as shown above

3. **Open your web browser**
   - Navigate to http://localhost:5000
   - You'll see the chat interface

4. **Start chatting**
   - Type your message in the input field
   - Press Enter or click "Send"
   - The AI will respond using the Ollama model

5. **Additional features**
   - Use the "Clear Conversation" button to reset the chat
   - Code blocks are automatically formatted with syntax highlighting
   - Click "Copy" on code blocks to copy code to clipboard

## Configuration

### Changing the AI Model
To use a different Ollama model, modify the `OLLAMA_MODEL` variable in either `app.py` or `botv2.py`:

```python
OLLAMA_MODEL = 'your-model-name:version'
```

### Changing the Ollama URL
If Ollama is running on a different port or host, modify the `OLLAMA_URL`:

```python
OLLAMA_URL = 'http://your-host:port/api/generate'
```

### Changing the Flask Port
If port 5000 is in use, modify the port in the Python files:

```python
app.run(debug=True, port=5001)  # Change port number as needed
```

## Troubleshooting

### Common Issues

1. **"Error communicating with Ollama"**
   - Ensure Ollama is running: `ollama serve`
   - Check if the model is installed: `ollama list`
   - Verify the model name in the code matches your installed model

2. **Port already in use**
   - Change the port in the Python file as shown in Configuration section
   - Or stop other services using port 5000

3. **Model not found**
   - Pull the required model: `ollama pull llama3.1:latest`
   - Or use a different model you have installed

4. **Python dependencies missing**
   - Install required packages: `pip install -r requirements.txt`

5. **Python not found**
   - Install Python from [python.org](https://www.python.org/downloads/)
   - Make sure to check "Add Python to PATH" during installation
   - Or disable Python app execution aliases in Windows Settings

### Checking Ollama Status
```bash
# Check if Ollama is running
ollama list

# Check available models
ollama ps

# Restart Ollama if needed
ollama serve
```

## File Structure

```
CodeReview/
├── app.py              # Main Flask application (local access only)
├── botv2.py            # Alternative version (network accessible)
├── requirements.txt    # Python dependencies
├── templates/
│   └── index.html      # Web interface template
└── README.md           # This file
```

## Technical Details

- **Backend**: Flask web framework
- **Frontend**: Vanilla JavaScript with Prism.js for syntax highlighting
- **API Endpoint**: Both versions use `/ask` endpoint for consistency
- **Data Format**: Frontend sends `{prompt: "user message"}` and expects `{response: "ai response"}`
- **Ollama Integration**: HTTP API calls to Ollama's generate endpoint

## Development

- The application uses Flask for the web framework
- Frontend uses vanilla JavaScript with Prism.js for syntax highlighting
- Communication with Ollama is done via HTTP API calls
- Both `app.py` and `botv2.py` use the same `/ask` endpoint for consistency
- The interface supports code block formatting with syntax highlighting and copy functionality

## License

This project is open source. Feel free to modify and distribute as needed. 