from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

OLLAMA_URL = 'http://localhost:11434/api/generate'
OLLAMA_MODEL = 'llama3.1:latest'

def ask_ollama(prompt):
    payload = {
        'model': OLLAMA_MODEL,
        'prompt': prompt,
        'stream': False
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get('response', 'No response from the model')
    except Exception as e:
        return f"Error communicating with Ollama: {e}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    user_prompt = request.json.get('prompt')
    if not user_prompt:
        return jsonify({'response': 'Prompt is missing.'}), 400
    
    ai_response = ask_ollama(user_prompt)
    return jsonify({'response': ai_response})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 
