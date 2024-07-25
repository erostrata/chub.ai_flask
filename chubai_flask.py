from flask import Flask, request, render_template, make_response
import requests
import json
import urllib.parse
import random
import re
from collections import OrderedDict

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
            char_title = data['node']['definition']['project_name']
            personality_raw = data['node']['definition']['personality']
            first_message_raw = data['node']['definition']['first_message']
            author = data['node']['fullPath']
            description = data['node']['tagline']

            def clean_data(d):
                clean = re.sub(r'https?://\S+|!\[.*?\]\(.*?\)', '', d)
                clean = clean.replace('\r', '').replace('\n', '').replace('{{user}}', 'user').replace('\u2019', "'").replace('\u2026', '...').replace('\u2014', '-').replace('{{char}}', char_title).replace('\\"', '"')
                return clean

            def replace_char_name_with_I(text, c):
                variations = [c.split()[0], c]
                pattern = re.compile("|".join(re.escape(variation) for variation in variations), re.IGNORECASE)
                text = pattern.sub("I", text)
                return text

            personality = clean_data(personality_raw)
            first_message = clean_data(first_message_raw).replace('*', '').replace('{{user}}', 'you')
            first_message = replace_char_name_with_I(first_message, char_title)

            prompt = OrderedDict([
                ("type", "duo-image"),
                ("model", "gpt-4o-mini"),
                ("state", "LIVE"),
                ("top_p", 0.8),
                ("memory", 20),
                ("prompt", 'You are now ' + char_title + '. ' + personality),
                ("greeting", first_message),
                ("temperature", 0.7)
            ])

            json_output = json.dumps(prompt, indent=2, ensure_ascii=False)
            json_output = re.sub(r'\\"', '', json_output)
            author_clean = re.sub(r'/.*', '', author)

            return {
                'author': author_clean,
                'description': description,
                'json_output': json_output
            }

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
        response = make_response(json.dumps({"error": "No base URL provided."}), 400)
        response.headers['Content-Type'] = 'application/json'
        return response
    
    api_url = construct_api_url(base_url)
    prompt = fetch_character_data(api_url)
    
    if 'error' in prompt:
        response = make_response(json.dumps(prompt), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

    formatted_response = f"Author: {prompt['author']}\n\nDescription: {prompt['description']}\n\nJSON:\n{prompt['json_output']}"
    
    response = make_response(formatted_response)
    response.headers['Content-Type'] = 'text/plain'
    
    return response

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)
