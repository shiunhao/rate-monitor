import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify
import os

app = Flask(__name__)

# 爬蟲核心
def get_google_rate(currency_pair):
    try:
        url = f"https://www.google.com/finance/quote/{currency_pair}"
        # 雲端 IP 容易被擋，這裡多加一些偽裝 Header
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")
        div = soup.find("div", {"class": "YMlKec fxKbKc"})
        if div:
            return float(div.text.replace(",", ""))
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

@app.route('/')
def home():
    return "Server is running!"

@app.route('/api/rates')
def get_rates():
    data = {
        "USD": get_google_rate("USD-TWD"),
        "KRW": get_google_rate("KRW-TWD")
    }
    response = jsonify(data)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)