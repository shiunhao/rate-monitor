import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, render_template_string
import os

app = Flask(__name__)

# --- 1. 爬蟲核心 ---
def get_google_rate(currency_pair):
    try:
        url = f"https://www.google.com/finance/quote/{currency_pair}"
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

# --- 2. 首頁 (RWD 自適應網頁) ---
@app.route('/')
def home():
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>匯率監控 Pro</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                background-color: #000000; 
                color: #ffffff; 
                margin: 0; 
                padding: 20px;
                display: flex;
                flex-direction: column;
                align-items: center;
                min-height: 100vh;
                box-sizing: border-box;
            }
            .select-container { width: 100%; max-width: 400px; margin-bottom: 20px; }
            select {
                width: 100%; padding: 12px; font-size: 18px; border-radius: 12px;
                border: none; background-color: #1c1c1e; color: white;
                appearance: none; text-align: center; font-weight: bold;
                box-shadow: 0 4px 12px rgba(255,255,255,0.1); outline: none;
            }
            .card-wrapper { width: 100%; max-width: 420px; display: none; animation: fadeIn 0.5s; }
            .card-wrapper.active { display: block; }
            @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
            .card {
                background-color: #1c1c1e; border-radius: 20px; padding: 25px;
                box-shadow: 0 8px 30px rgba(0,0,0,0.5); text-align: center;
                border: 2px solid transparent; transition: border-color 0.3s;
            }
            .card.alert { border-color: #ff453a; box-shadow: 0 0 30px rgba(255, 69, 58, 0.3); }
            .rate-display { font-size: 4rem; font-weight: 800; margin: 10px 0; font-family: SF Mono, Consolas, monospace; letter-spacing: -2px; }
            .rate-up { color: #ff453a; }
            .rate-down { color: #30d158; }
            .chart-box { height: 200px; width: 100%; margin: 20px 0; }
            .settings { background-color: #2c2c2e; padding: 15px; border-radius: 12px; margin-top: 10px; }
            .row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; font-size: 15px; color: #aeaeb2; }
            input[type="number"] {
                background: #000; border: 1px solid #48484a; color: white;
                padding: 10px; border-radius: 8px; width: 100px; text-align: center; font-size: 16px;
            }
            .status-bar { margin-top: 30px; font-size: 12px; color: #636366; display: flex; align-items: center; gap: 5px; }
            .dot { width: 8px; height: 8px; background: #30d158; border-radius: 50%; display: inline-block; }
            .dot.error { background: #ff453a; }
            @media (max-width: 600px) { body { padding: 15px; } .rate-display { font-size: 3.5rem; } .card { padding: 20px; } }
        </style>
    </head>
    <body>
        <div class="select-container">
            <select id="currencySelect" onchange="switchCurrency()">
                <option value="USD">🇺🇸 美金 (USD/TWD)</option>
                <option value="KRW">🇰🇷 韓元 (KRW/TWD)</option>
            </select>
        </div>

        <div id="wrap-USD" class="card-wrapper active">
            <div class="card" id="card-USD">
                <div class="rate-display" id="rate-USD">--.--</div>
                <div class="chart-box"><canvas id="chart-USD"></canvas></div>
                <div class="settings">
                    <div class="row"><span>🔔 高於通知</span><input type="number" id="h-USD" step="0.01" placeholder="32.50"></div>
                    <div class="row"><span>🔔 低於通知</span><input type="number" id="l-USD" step="0.01" placeholder="31.80"></div>
                </div>
            </div>
        </div>

        <div id="wrap-KRW" class="card-wrapper">
            <div class="card" id="card-KRW">
                <div class="rate-display" id="rate-KRW">--.--</div>
                <div class="chart-box"><canvas id="chart-KRW"></canvas></div>
                <div class="settings">
                    <div class="row"><span>🔔 高於通知</span><input type="number" id="h-KRW" step="0.0001" placeholder="0.0250"></div>
                    <div class="row"><span>🔔 低於通知</span><input type="number" id="l-KRW" step="0.0001" placeholder="0.0210"></div>
                </div>
            </div>
        </div>

        <div class="status-bar">
            <span id="status-dot" class="dot"></span>
            <span id="status-text">連線中...</span>
        </div>

        <script>
            const API_URL = '/api/rates';
            let charts = {}, lastRates = { USD: 0, KRW: 0 };

            function switchCurrency() {
                const selected = document.getElementById('currencySelect').value;
                document.querySelectorAll('.card-wrapper').forEach(el => el.classList.remove('active'));
                document.getElementById('wrap-' + selected).classList.add('active');
            }

            function initChart(id, color) {
                const ctx = document.getElementById(id).getContext('2d');
                return new Chart(ctx, {
                    type: 'line',
                    data: { labels: [], datasets: [{ data: [], borderColor: color, borderWidth: 3, pointRadius: 0, tension: 0.4, fill: false }] },
                    options: {
                        responsive: true, maintainAspectRatio: false, plugins: { legend: false },
                        scales: { x: { display: false }, y: { grid: { color: '#333' }, ticks: { color: '#888' } } }, animation: false
                    }
                });
            }
            charts.USD = initChart('chart-USD', '#0a84ff');
            charts.KRW = initChart('chart-KRW', '#bf5af2');

            function checkAlert(cur, rate) {
                const h = parseFloat(document.getElementById('h-'+cur).value);
                const l = parseFloat(document.getElementById('l-'+cur).value);
                const card = document.getElementById('card-'+cur);
                if ((!isNaN(h) && rate >= h) || (!isNaN(l) && rate <= l)) card.classList.add('alert');
                else card.classList.remove('alert');
            }

            async function update() {
                const statusText = document.getElementById('status-text');
                const statusDot = document.getElementById('status-dot');
                try {
                    let res = await fetch(API_URL);
                    let data = await res.json();
                    statusText.innerText = "最後更新: " + new Date().toLocaleTimeString();
                    statusDot.classList.remove('error');
                    ['USD', 'KRW'].forEach(cur => {
                        const rate = data[cur];
                        if(!rate) return;
                        const el = document.getElementById('rate-'+cur);
                        const prev = lastRates[cur];
                        el.innerText = rate;
                        el.classList.remove('rate-up', 'rate-down');
                        if(prev && rate > prev) el.classList.add('rate-up');
                        if(prev && rate < prev) el.classList.add('rate-down');
                        lastRates[cur] = rate;
                        const c = charts[cur];
                        c.data.labels.push('');
                        c.data.datasets[0].data.push(rate);
                        if(c.data.labels.length > 30) { c.data.labels.shift(); c.data.datasets[0].data.shift(); }
                        c.update();
                        checkAlert(cur, rate);
                    });
                } catch(e) {
                    statusText.innerText = "連線中斷...";
                    statusDot.classList.add('error');
                }
            }
            setInterval(update, 10000);
            update();
        </script>
    </body>
    </html>
    """
    return render_template_string(html_content)

# --- 3. API 接口 ---
@app.route('/api/rates')
def get_rates():
    data = {
        "USD": get_google_rate("USD-TWD"),
        "KRW": get_google_rate("KRW-TWD")
    }
    return jsonify(data)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
