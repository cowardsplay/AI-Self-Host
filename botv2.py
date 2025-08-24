from flask import Flask, render_template, request, jsonify
import requests
import logging
import os
import subprocess
import json
import time
import sys
from urllib.parse import urlparse
import re

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

OLLAMA_URL = 'http://localhost:11434/api/generate'
OLLAMA_MODEL = 'llama3.1:latest'  # You can change this to your available model

# Wiki.js API Configuration
WIKIJS_BASE_URL = 'http://192.168.5.66:3000'
WIKIJS_API_KEY = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcGkiOjIsImdycCI6MSwiaWF0IjoxNzUzOTIzMDg4LCJleHAiOjE4NDg1OTU4ODgsImF1ZCI6InVybjp3aWtpLmpzIiwiaXNzIjoidXJuOndpa2kuanMifQ.nnHZrkCTj8zpxEm8Y3NNBIOkEubVd42j0yN4rydb3fl3IA3PYjQzUjuExwGp3ATw5EHUhOli7ZVVHuBTv4DaFboalOiurtGI0DnPE0971ZGfyKOaofvTP4-AH4MOPS_HKYrXbJMTLFCDmBL0ulJcZc_AzySuZunsR_njfYMlIcBPsukgqCnfiLTc8p_UvVH6imsAMIKzZCFioMqV6YrimpDS11kH8YOZ7gFGv0sDvzKzcGxqYd0oe-_1j50XPr6PXCIXwbJo_Pek_a2X9xbW7ZIIbzXh-6TNjEkhwS_pKmF1otM-rxQPdSO4Yykfp0rm91CjQ2QZwtssPOsRyL00uQ'

def fetch_wikijs_content(url, timeout=10):
    """Fetch content from Wiki.js using the API"""
    try:
        logger.info(f"Fetching Wiki.js content from: {url}")
        
        # Extract path from URL
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        # Try different API endpoints
        api_endpoints = [
            f"{WIKIJS_BASE_URL}/api/content/pages",
            f"{WIKIJS_BASE_URL}/api/pages",
            f"{WIKIJS_BASE_URL}/api/content",
            f"{WIKIJS_BASE_URL}/api"
        ]
        
        headers = {
            'Authorization': f'Bearer {WIKIJS_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Try each endpoint until one works
        for api_endpoint in api_endpoints:
            try:
                logger.info(f"Trying API endpoint: {api_endpoint}")
                response = requests.get(api_endpoint, headers=headers, timeout=timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Successfully fetched Wiki.js content from {api_endpoint}: {len(str(data))} characters")
                    
                    # Format the content for better readability
                    if isinstance(data, list):
                        # Multiple pages
                        content = "Available pages:\n"
                        for page in data:
                            content += f"- {page.get('title', 'Untitled')}: {page.get('description', 'No description')}\n"
                    elif isinstance(data, dict):
                        # Single page
                        content = f"Page: {data.get('title', 'Untitled')}\n"
                        content += f"Description: {data.get('description', 'No description')}\n"
                        content += f"Content: {data.get('content', 'No content')}\n"
                        if 'tags' in data and data['tags']:
                            content += f"Tags: {', '.join(data['tags'])}\n"
                    else:
                        content = str(data)
                    
                    return content
                else:
                    logger.warning(f"API endpoint {api_endpoint} returned status {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"Failed to access {api_endpoint}: {e}")
                continue
        
        # If all API endpoints fail, try the regular web interface
        logger.info("All API endpoints failed, trying web interface")
        web_response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=timeout)
        
        if web_response.status_code == 200:
            content = extract_text_from_html(web_response.text)
            return f"Web interface content:\n{content}"
        else:
            return f"Error: All Wiki.js endpoints returned errors. Last status: {web_response.status_code}"
            
    except requests.exceptions.ConnectionError:
        logger.error(f"Cannot connect to Wiki.js API at {url}")
        return f"Error: Cannot connect to Wiki.js API. Check if the server is running and accessible."
    except requests.exceptions.Timeout:
        logger.error(f"Timeout when fetching Wiki.js content from {url}")
        return f"Error: Timeout when accessing Wiki.js API"
    except Exception as e:
        logger.error(f"Error fetching Wiki.js content from {url}: {e}")
        return f"Error: {e}"

def search_wikijs_content(search_term):
    """Search for content within Wiki.js pages"""
    try:
        logger.info(f"Searching Wiki.js content for: {search_term}")
        
        # Try different API endpoints for search
        api_endpoints = [
            f"{WIKIJS_BASE_URL}/api/content/pages",
            f"{WIKIJS_BASE_URL}/api/pages",
            f"{WIKIJS_BASE_URL}/api/content",
            f"{WIKIJS_BASE_URL}/api"
        ]
        
        headers = {
            'Authorization': f'Bearer {WIKIJS_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Try each endpoint until one works
        for api_endpoint in api_endpoints:
            try:
                logger.info(f"Trying search API endpoint: {api_endpoint}")
                response = requests.get(api_endpoint, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    search_term_lower = search_term.lower()
                    
                    # Search through pages
                    matching_content = []
                    
                    if isinstance(data, list):
                        for page in data:
                            title = page.get('title', '').lower()
                            description = page.get('description', '').lower()
                            content = page.get('content', '').lower()
                            
                            # Check if search term appears in title, description, or content
                            if (search_term_lower in title or 
                                search_term_lower in description or 
                                search_term_lower in content):
                                
                                matching_content.append({
                                    'title': page.get('title', 'Untitled'),
                                    'description': page.get('description', 'No description'),
                                    'content': page.get('content', 'No content')[:500] + '...' if len(page.get('content', '')) > 500 else page.get('content', 'No content'),
                                    'path': page.get('path', ''),
                                    'tags': page.get('tags', [])
                                })
                    
                    if matching_content:
                        result = f"Found {len(matching_content)} matching pages for '{search_term}':\n\n"
                        for item in matching_content:
                            result += f"Title: {item['title']}\n"
                            result += f"Description: {item['description']}\n"
                            result += f"Content: {item['content']}\n"
                            if item['tags']:
                                result += f"Tags: {', '.join(item['tags'])}\n"
                            result += "\n" + "-"*50 + "\n\n"
                        return result
                    else:
                        return f"No content found matching '{search_term}' in Wiki.js pages."
                        
                else:
                    logger.warning(f"Search API endpoint {api_endpoint} returned status {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"Failed to search {api_endpoint}: {e}")
                continue
        
        return f"Error: All Wiki.js API endpoints failed for search"
            
    except Exception as e:
        logger.error(f"Error searching Wiki.js content: {e}")
        return f"Error: {e}"

def is_wikijs_url(url):
    """Check if the URL is a Wiki.js URL"""
    return '192.168.5.66:3000' in url or 'wikijs' in url.lower()

def extract_text_from_html(html_content, max_length=1500):
    """Extract meaningful text from HTML content using regex"""
    try:
        # Remove script and style tags
        text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Decode HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        return text
    except Exception as e:
        logger.warning(f"Failed to parse HTML, using raw content: {e}")
        # Fallback: return first part of raw content
        return html_content[:max_length] + "..." if len(html_content) > max_length else html_content

def fetch_url_content(url, timeout=10):
    """Fetch content from a URL"""
    try:
        logger.info(f"Fetching content from: {url}")
        
        # Check if it's a Wiki.js URL and use API if available
        if is_wikijs_url(url):
            logger.info("Detected Wiki.js URL, using API")
            return fetch_wikijs_content(url, timeout)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        
        if response.status_code == 200:
            content = response.text
            logger.info(f"Successfully fetched {len(content)} characters from {url}")
            
            # Extract meaningful text from HTML
            if 'text/html' in response.headers.get('content-type', ''):
                text_content = extract_text_from_html(content)
                logger.info(f"Extracted {len(text_content)} characters of meaningful text")
                return text_content
            else:
                return content
        else:
            logger.error(f"HTTP {response.status_code} when fetching {url}")
            return f"Error: HTTP {response.status_code} when accessing {url}"
            
    except requests.exceptions.ConnectionError:
        logger.error(f"Cannot connect to {url}")
        return f"Error: Cannot connect to {url}. Check if the server is running and accessible."
    except requests.exceptions.Timeout:
        logger.error(f"Timeout when fetching {url}")
        return f"Error: Timeout when accessing {url}"
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return f"Error: {e}"

def extract_url_from_prompt(prompt):
    """Extract URL from prompt if it contains one"""
    import re
    url_pattern = r'https?://[^\s]+'
    urls = re.findall(url_pattern, prompt)
    return urls[0] if urls else None

def ask_ollama_with_context(prompt, context=""):
    """Ask Ollama with additional context"""
    if context:
        # Create a more focused prompt with limited context
        full_prompt = f"Based on this content from a webpage:\n\n{context}\n\nUser question: {prompt}\n\nPlease provide a helpful answer based on the content above."
    else:
        full_prompt = prompt
    
    return ask_ollama(full_prompt)

def ask_ollama_simple(prompt):
    """Simplified Ollama communication without warmup or complex fallbacks"""
    try:
        logger.info(f"Simple Ollama request for: {prompt[:50]}...")
        
        # Use subprocess with proper encoding for Windows
        if sys.platform == "win32":
            # Windows-specific encoding handling
            result = subprocess.run(
                ['ollama', 'run', OLLAMA_MODEL, prompt],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',  # Replace problematic characters
                timeout=90,  # Increased timeout to 90 seconds
                creationflags=subprocess.CREATE_NO_WINDOW  # Hide console window on Windows
            )
        else:
            # Unix/Linux handling
            result = subprocess.run(
                ['ollama', 'run', OLLAMA_MODEL, prompt],
                capture_output=True,
                text=True,
                timeout=90  # Increased timeout to 90 seconds
            )
        
        if result.returncode == 0:
            response = result.stdout.strip()
            logger.info(f"Ollama response received: {response[:100]}...")
            return response
        else:
            error_msg = f"Ollama CLI failed: {result.stderr}"
            logger.error(error_msg)
            return error_msg
            
    except subprocess.TimeoutExpired:
        logger.error("Ollama request timed out")
        return "Error: Request timed out after 90 seconds"
    except FileNotFoundError:
        logger.error("Ollama not found. Please install Ollama first.")
        return "Error: Ollama not found. Please install Ollama from https://ollama.ai/"
    except Exception as e:
        logger.error(f"Ollama request error: {e}")
        return f"Error: {e}"

def ask_ollama_http(prompt):
    """HTTP API method as backup"""
    try:
        logger.info(f"HTTP API request for: {prompt[:50]}...")
        
        payload = {
            'model': OLLAMA_MODEL,
            'prompt': prompt,
            'stream': False
        }
        
        response = requests.post(
            OLLAMA_URL, 
            json=payload, 
            timeout=60,  # Increased timeout to 60 seconds
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'response' in data:
                logger.info("HTTP API response received")
                return data['response']
            else:
                logger.error(f"Unexpected HTTP response format: {data}")
                return "Error: Unexpected response format"
        else:
            logger.error(f"HTTP API failed with status {response.status_code}")
            return f"Error: HTTP API returned status {response.status_code}"
            
    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to Ollama HTTP API")
        return "Error: Cannot connect to Ollama. Please make sure Ollama is running on localhost:11434"
    except Exception as e:
        logger.error(f"HTTP API error: {e}")
        return f"Error: HTTP API failed - {e}"

def check_ollama_available():
    """Check if Ollama is available and running"""
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=5
            )
        
        return result.returncode == 0
    except Exception:
        return False

def ask_ollama(prompt):
    """Main function that tries CLI first, then HTTP"""
    logger.info(f"Processing prompt: {prompt[:50]}...")
    
    # Check if Ollama is available first
    if not check_ollama_available():
        return "Error: Ollama is not available. Please make sure Ollama is installed and running."
    
    # Try CLI method first (most reliable)
    result = ask_ollama_simple(prompt)
    
    # If CLI fails, try HTTP
    if result.startswith("Error:"):
        logger.info("CLI failed, trying HTTP API...")
        result = ask_ollama_http(prompt)
    
    return result

def should_fetch_wikijs_content(prompt):
    """Determine if we should fetch Wiki.js content based on the prompt"""
    prompt_lower = prompt.lower()
    
    # Keywords that suggest the user wants Wiki.js content
    wiki_keywords = [
        'wikijs', 'wiki.js', 'wiki', 'homepage', 'synapsetechlab', 'dc1',
        'content', 'information', 'documentation', 'server', 'network',
        'ip address', 'ip', 'address', 'synapse', 'tech', 'lab'
    ]
    
    # Check if any Wiki.js related keywords are in the prompt
    for keyword in wiki_keywords:
        if keyword in prompt_lower:
            return True
    
    return False

def fetch_wikijs_homepage():
    """Fetch the Wiki.js homepage content"""
    try:
        logger.info("Fetching Wiki.js homepage content")
        
        # Try different API endpoints
        api_endpoints = [
            f"{WIKIJS_BASE_URL}/api/content/pages",
            f"{WIKIJS_BASE_URL}/api/pages",
            f"{WIKIJS_BASE_URL}/api/content",
            f"{WIKIJS_BASE_URL}/api"
        ]
        
        headers = {
            'Authorization': f'Bearer {WIKIJS_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Try each endpoint until one works
        for api_endpoint in api_endpoints:
            try:
                logger.info(f"Trying homepage API endpoint: {api_endpoint}")
                response = requests.get(api_endpoint, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Format the content for better readability
                    if isinstance(data, list):
                        content = "Available Wiki.js pages:\n"
                        for page in data:
                            content += f"- {page.get('title', 'Untitled')}: {page.get('description', 'No description')}\n"
                            if page.get('content'):
                                content += f"  Content: {page.get('content', '')[:200]}...\n"
                    elif isinstance(data, dict):
                        content = f"Page: {data.get('title', 'Untitled')}\n"
                        content += f"Description: {data.get('description', 'No description')}\n"
                        content += f"Content: {data.get('content', 'No content')}\n"
                        if 'tags' in data and data['tags']:
                            content += f"Tags: {', '.join(data['tags'])}\n"
                    else:
                        content = str(data)
                    
                    return content
                else:
                    logger.warning(f"Homepage API endpoint {api_endpoint} returned status {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"Failed to access homepage {api_endpoint}: {e}")
                continue
        
        # If all API endpoints fail, try the web interface
        logger.info("All API endpoints failed, trying web interface for homepage")
        web_response = requests.get(f"{WIKIJS_BASE_URL}/", headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        
        if web_response.status_code == 200:
            content = extract_text_from_html(web_response.text)
            return f"Wiki.js homepage content:\n{content}"
        else:
            return f"Error: All Wiki.js endpoints failed. Last status: {web_response.status_code}"
            
    except Exception as e:
        logger.error(f"Error fetching Wiki.js homepage: {e}")
        return f"Error: {e}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test')
def test():
    return render_template('test.html')

@app.route('/test-wiki', methods=['GET'])
def test_wiki():
    """Test connectivity to Wiki.js server"""
    wiki_url = "http://192.168.5.66:3000"
    
    try:
        logger.info(f"Testing connectivity to Wiki.js at {wiki_url}")
        
        # Test basic connectivity
        response = requests.get(wiki_url, timeout=5)
        
        if response.status_code == 200:
            return jsonify({
                'status': 'success',
                'message': f'Successfully connected to Wiki.js at {wiki_url}',
                'status_code': response.status_code,
                'content_length': len(response.text),
                'content_preview': response.text[:500] + '...' if len(response.text) > 500 else response.text
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Wiki.js responded with status code {response.status_code}',
                'status_code': response.status_code
            })
            
    except requests.exceptions.ConnectionError as e:
        return jsonify({
            'status': 'error',
            'message': f'Cannot connect to Wiki.js at {wiki_url}',
            'error': str(e),
            'suggestions': [
                'Check if Wiki.js is running on the target machine',
                'Verify the IP address is correct',
                'Check if port 3000 is open and accessible',
                'Ensure both machines are on the same subnet',
                'Check Windows Firewall settings'
            ]
        })
    except requests.exceptions.Timeout as e:
        return jsonify({
            'status': 'error',
            'message': f'Timeout when connecting to Wiki.js at {wiki_url}',
            'error': str(e)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Unexpected error when connecting to Wiki.js',
            'error': str(e)
        })

@app.route('/test-wiki-api', methods=['GET'])
def test_wiki_api():
    """Test Wiki.js API functionality"""
    try:
        logger.info("Testing Wiki.js API functionality")
        
        # Try different API endpoints
        api_endpoints = [
            f"{WIKIJS_BASE_URL}/api/content/pages",
            f"{WIKIJS_BASE_URL}/api/pages",
            f"{WIKIJS_BASE_URL}/api/content",
            f"{WIKIJS_BASE_URL}/api"
        ]
        
        headers = {
            'Authorization': f'Bearer {WIKIJS_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Try each endpoint until one works
        for api_endpoint in api_endpoints:
            try:
                logger.info(f"Testing API endpoint: {api_endpoint}")
                response = requests.get(api_endpoint, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Format the response
                    if isinstance(data, list):
                        pages_info = []
                        for page in data:
                            pages_info.append({
                                'title': page.get('title', 'Untitled'),
                                'path': page.get('path', ''),
                                'description': page.get('description', 'No description'),
                                'tags': page.get('tags', [])
                            })
                        
                        return jsonify({
                            'status': 'success',
                            'message': f'Successfully connected to Wiki.js API at {api_endpoint}',
                            'total_pages': len(data),
                            'pages': pages_info
                        })
                    else:
                        return jsonify({
                            'status': 'success',
                            'message': f'Successfully connected to Wiki.js API at {api_endpoint}',
                            'data': data
                        })
                else:
                    logger.warning(f"API endpoint {api_endpoint} returned status {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"Failed to test {api_endpoint}: {e}")
                continue
        
        # If all API endpoints fail, try web interface
        logger.info("All API endpoints failed, trying web interface")
        web_response = requests.get(f"{WIKIJS_BASE_URL}/", headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        
        if web_response.status_code == 200:
            return jsonify({
                'status': 'success',
                'message': 'Successfully connected to Wiki.js web interface (API endpoints not available)',
                'content_preview': extract_text_from_html(web_response.text)[:500] + '...'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'All Wiki.js endpoints failed. Last status: {web_response.status_code}',
                'status_code': web_response.status_code
            })
            
    except requests.exceptions.ConnectionError as e:
        return jsonify({
            'status': 'error',
            'message': f'Cannot connect to Wiki.js API',
            'error': str(e),
            'suggestions': [
                'Check if Wiki.js is running on the target machine',
                'Verify the API key is correct',
                'Check if the API endpoint is accessible',
                'Ensure both machines are on the same subnet'
            ]
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Unexpected error when testing Wiki.js API',
            'error': str(e)
        })

@app.route('/wiki-pages', methods=['GET'])
def list_wiki_pages():
    """List all available Wiki.js pages"""
    try:
        # Try different API endpoints
        api_endpoints = [
            f"{WIKIJS_BASE_URL}/api/content/pages",
            f"{WIKIJS_BASE_URL}/api/pages",
            f"{WIKIJS_BASE_URL}/api/content",
            f"{WIKIJS_BASE_URL}/api"
        ]
        
        headers = {
            'Authorization': f'Bearer {WIKIJS_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Try each endpoint until one works
        for api_endpoint in api_endpoints:
            try:
                logger.info(f"Listing pages from: {api_endpoint}")
                response = requests.get(api_endpoint, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    return jsonify({
                        'status': 'success',
                        'pages': data
                    })
                else:
                    logger.warning(f"API endpoint {api_endpoint} returned status {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"Failed to list pages from {api_endpoint}: {e}")
                continue
        
        # If all API endpoints fail, try web interface
        logger.info("All API endpoints failed, trying web interface for pages")
        web_response = requests.get(f"{WIKIJS_BASE_URL}/", headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        
        if web_response.status_code == 200:
            content = extract_text_from_html(web_response.text)
            return jsonify({
                'status': 'success',
                'pages': [{'title': 'Homepage', 'content': content[:1000] + '...' if len(content) > 1000 else content}]
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Failed to fetch pages: {web_response.status_code}'
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error: {str(e)}'
        })

@app.route('/fetch-url', methods=['POST'])
def fetch_url():
    """Fetch content from a URL"""
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    # Validate URL
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return jsonify({'error': 'Invalid URL format'}), 400
    except Exception:
        return jsonify({'error': 'Invalid URL format'}), 400
    
    content = fetch_url_content(url)
    return jsonify({'content': content})

@app.route('/ask', methods=['POST'])
def ask():
    user_prompt = request.json.get('prompt')
    if not user_prompt:
        return jsonify({'response': 'Prompt is missing.'}), 400
    
    logger.info(f"Received prompt: {user_prompt}")
    
    # Check if prompt contains a URL
    url = extract_url_from_prompt(user_prompt)
    
    if url:
        logger.info(f"Detected URL in prompt: {url}")
        
        # Fetch content from the URL
        url_content = fetch_url_content(url)
        
        if url_content.startswith("Error:"):
            # If we can't fetch the URL, just ask Ollama about it
            ai_response = ask_ollama(user_prompt)
        else:
            # Use the extracted text content (already limited in size)
            ai_response = ask_ollama_with_context(user_prompt, url_content)
    elif should_fetch_wikijs_content(user_prompt):
        logger.info("Detected Wiki.js related prompt, searching for relevant content")
        
        # First try to search for specific content
        search_content = search_wikijs_content(user_prompt)
        
        if search_content.startswith("Error:"):
            # If search fails, fall back to homepage content
            wiki_content = fetch_wikijs_homepage()
        else:
            wiki_content = search_content
        
        if wiki_content.startswith("Error:"):
            # If we can't fetch Wiki.js content, just ask Ollama
            ai_response = ask_ollama(user_prompt)
        else:
            # Provide Wiki.js content as context
            context_prompt = f"Based on this Wiki.js content:\n\n{wiki_content}\n\nUser question: {user_prompt}\n\nPlease answer based on the Wiki.js content above. If the information is not available in the content, please say so."
            ai_response = ask_ollama_with_context(user_prompt, wiki_content)
    else:
        # Regular prompt without URL or Wiki.js context
        ai_response = ask_ollama(user_prompt)
    
    logger.info(f"AI response: {ai_response}")
    
    return jsonify({'response': ai_response})

@app.route('/search-wiki', methods=['POST'])
def search_wiki():
    """Search Wiki.js content"""
    data = request.json
    search_term = data.get('search_term', '')
    
    if not search_term:
        return jsonify({'error': 'Search term is required'}), 400
    
    content = search_wikijs_content(search_term)
    return jsonify({'content': content})

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        ollama_available = check_ollama_available()
        
        if ollama_available:
            return jsonify({
                'status': 'healthy',
                'ollama_available': True,
                'model': OLLAMA_MODEL
            })
        else:
            return jsonify({
                'status': 'unhealthy',
                'ollama_available': False,
                'error': 'Ollama not available'
            })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'ollama_available': False,
            'error': str(e)
        })

@app.route('/test-simple', methods=['POST'])
def test_simple():
    """Simple test endpoint"""
    try:
        simple_prompt = "Say hello in one sentence."
        result = ask_ollama_simple(simple_prompt)
        return jsonify({'response': result})
    except Exception as e:
        return jsonify({'response': f"Error: {e}"})

@app.route('/models', methods=['GET'])
def list_models():
    """List available Ollama models"""
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=10
            )
        
        if result.returncode == 0:
            return jsonify({
                'status': 'success',
                'models': result.stdout
            })
        else:
            return jsonify({
                'status': 'error',
                'error': result.stderr
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        })

@app.route('/debug-wiki-api', methods=['GET'])
def debug_wiki_api():
    """Debug Wiki.js API endpoints to discover what's available"""
    try:
        logger.info("Debugging Wiki.js API endpoints")
        
        # Common Wiki.js API endpoints to test
        test_endpoints = [
            f"{WIKIJS_BASE_URL}/api/content/pages",
            f"{WIKIJS_BASE_URL}/api/pages",
            f"{WIKIJS_BASE_URL}/api/content",
            f"{WIKIJS_BASE_URL}/api",
            f"{WIKIJS_BASE_URL}/api/v1/pages",
            f"{WIKIJS_BASE_URL}/api/v1/content",
            f"{WIKIJS_BASE_URL}/api/v2/pages",
            f"{WIKIJS_BASE_URL}/api/v2/content"
        ]
        
        headers = {
            'Authorization': f'Bearer {WIKIJS_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        results = []
        
        for endpoint in test_endpoints:
            try:
                logger.info(f"Testing endpoint: {endpoint}")
                response = requests.get(endpoint, headers=headers, timeout=5)
                
                result = {
                    'endpoint': endpoint,
                    'status_code': response.status_code,
                    'success': response.status_code == 200,
                    'content_type': response.headers.get('content-type', 'unknown'),
                    'content_length': len(response.text) if response.text else 0
                }
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        result['data_type'] = type(data).__name__
                        result['data_preview'] = str(data)[:200] + '...' if len(str(data)) > 200 else str(data)
                    except:
                        result['data_type'] = 'not_json'
                        result['data_preview'] = response.text[:200] + '...' if len(response.text) > 200 else response.text
                else:
                    result['error'] = response.text[:200] + '...' if len(response.text) > 200 else response.text
                
                results.append(result)
                
            except Exception as e:
                results.append({
                    'endpoint': endpoint,
                    'status_code': 'error',
                    'success': False,
                    'error': str(e)
                })
        
        # Also test without API key
        try:
            no_auth_response = requests.get(f"{WIKIJS_BASE_URL}/api", timeout=5)
            results.append({
                'endpoint': f"{WIKIJS_BASE_URL}/api (no auth)",
                'status_code': no_auth_response.status_code,
                'success': no_auth_response.status_code == 200,
                'content_type': no_auth_response.headers.get('content-type', 'unknown'),
                'content_length': len(no_auth_response.text) if no_auth_response.text else 0
            })
        except Exception as e:
            results.append({
                'endpoint': f"{WIKIJS_BASE_URL}/api (no auth)",
                'status_code': 'error',
                'success': False,
                'error': str(e)
            })
        
        return jsonify({
            'status': 'success',
            'message': 'Wiki.js API endpoint debugging completed',
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error debugging Wiki.js API: {str(e)}'
        })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 
