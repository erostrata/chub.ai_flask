import requests
import json
import urllib.parse
import random
from collections import OrderedDict
from flask import Flask, request, render_template, jsonify

app = Flask(__name__)

def fetch_character_data(url):
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'ch-api-key': 'glpat-UZXEBupEVv2vMCdFDkfJ',
        'origin': 'https://chub.ai',
        'priority': 'u=1, i',
        'referer': 'https://chub.ai/',
        'samwise': 'glpat-UZXEBupEVv2vMCdFDkfJ',
        'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        try:
            data = response.json()
            personality = data['node']['definition']['personality']
            description = data['node']['definition']['description']
            first_message = data['node']['definition']['first_message']

            # Create the JSON prompt using OrderedDict to maintain the order
            prompt = OrderedDict([
                ("type", "duo-image"),
                ("model", "gpt-4-0314"),
                ("state", "LIVE"),
                ("top_p", 0.8),
                ("memory", 20),
                ("prompt", description + personality),
                ("greeting", first_message),
                ("temperature", 0.7)
            ])

            return prompt
        except json.JSONDecodeError:
            return {"error": "Failed to decode JSON response."}
    else:
        return {"error": f"Failed to retrieve the data. Status code: {response.status_code}"}

def construct_api_url(base_url):
    parsed_url = urllib.parse.urlparse(base_url)
    path = parsed_url.path
    api_base_url = f"https://api.chub.ai/api{path}"
    nocache_value = random.random()
    api_url = f"{api_base_url}?full=true&nocache={nocache_value}"
    return api_url

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/fetch', methods=['POST'])
def fetch():
    base_url = request.form.get('base_url')
    if not base_url:
        return jsonify({"error": "No base URL provided."}), 400
    
    api_url = construct_api_url(base_url)
    prompt = fetch_character_data(api_url)
    
    # Convert the OrderedDict to a JSON string with indentation
    formatted_json = json.dumps(prompt, indent=2)
    return formatted_json, 200, {'Content-Type': 'application/json'}

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)
