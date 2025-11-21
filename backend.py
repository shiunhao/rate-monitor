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

# --- 2. 首頁 (直接回傳 HTML 網頁) ---
@app.route('/')
def home():
    # 這裡放的是你原本 index.html 的內容
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>雲端匯率監控</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: 'Microsoft JhengHei', 'Segoe UI', sans-serif; background: #1a1a1a; color: white; padding: 20px; text-align: center; }
            h2 { margin-bottom: 5px; }
            .sub { color: #aaa; font-size: 12px; margin-bottom: 20px; }
            .container { display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; }
            .card { 
                background: #2d2d2d; border-radius: 15px; padding: 20px; width: 320px; 
                border: 2px solid transparent; box-shadow: 0 4px 10px rgba(0,0,0,0.3); margin-bottom: 20px;
            }
            .card.alert { border-color: #ff4444; box-shadow: 0 0 20px rgba(255, 68, 68, 0.4); animation: pulse 1s infinite; }
            @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.02); } 100% { transform: scale(1); } }
            .rate { font-size: 3.5rem; font-weight: bold; margin: 15px 0; font-family: monospace; }
            .rate-up { color: #ff5252; }   
            .rate-down { color: #00e676; } 
            .settings { background: #3d3d3d; padding: 10px; border-radius: 8px; margin-top: 15px; }
            .input-row { display: flex; justify-content: space-between; align-items: center; margin: 5px 0; font-size: 14px; }
            input { background: #555; border: 1px solid #666; color: white; padding: 5px; width: 80px; text-align: center; border-radius: 4px; }
            .status-box { margin-top: 20px; padding: 10px; font-size: 12px; color: #888; }
            .spinner { display: inline-block; animation: spin 2s linear infinite; margin-right: 5px; display: none; }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        </style>
    </head>
    <body>
        <h2>Google Finance 全端監控</h2>
        <div class="sub">資料來源: Python Server (Render Cloud)</div>
        
        <div class="container">
            <div class="card" id="card-USD">
                <h3>🇺🇸 美金 (USD)</h3>
                <div id="rate-USD" class="rate">--.--</div>
                <canvas id="chart-USD" height="150"></canvas>
                <div class="settings">
                    <div class="input-row">🔔 高於通知 <input type="number" id="h-USD" step="0.01" placeholder="32.5"></div>
                    <div class="input-row">🔔 低於通知 <input type="number" id="l-USD" step="0.01" placeholder="31.8"></div>
                </div>
            </div>
            <div class="card" id="card-KRW">
                <h3>🇰🇷 韓元 (KRW)</h3>
                <div id="rate-KRW" class="rate">--.--</div>
                <canvas id="chart-KRW" height="150"></canvas>
                <div class="settings">
                    <div class="input-row">🔔 高於通知 <input type="number" id="h-KRW" step="0.0001" placeholder="0.025"></div>
                    <div class="input-row">🔔 低於通知 <input type="number" id="l-KRW" step="0.0001" placeholder="0.021"></div>
                </div>
            </div>
        </div>

        <div class="status-box">
            <span id="spinner" class="spinner">⏳</span>
            <span id="status-text">正在連線...</span>
        </div>

        <script>
            // 自動指向同一個網站的 API
            const API_URL = '/api/rates';

            let charts = {}, lastRates = {USD:0, KRW:0};
            
            function initChart(id, color) {
                return new Chart(document.getElementById(id), {
                    type: 'line',
                    data: { labels: [], datasets: [{ data: [], borderColor: color, borderWidth:2, fill: false, pointRadius: 0 }] },
                    options: { plugins:{legend:false}, scales:{x:{display:false}, y:{grid:{color:'#444'}}}, animation: false }
                });
            }
            charts.USD = initChart('chart-USD', '#2196F3');
            charts.KRW = initChart('chart-KRW', '#9C27B0');

            function checkAlert(cur, rate) {
                let h = parseFloat(document.getElementById('h-'+cur).value);
                let l = parseFloat(document.getElementById('l-'+cur).value);
                let card = document.getElementById('card-'+cur);
                if ((!isNaN(h) && rate >= h) || (!isNaN(l) && rate <= l)) card.classList.add('alert');
                else card.classList.remove('alert');
            }

            async function update() {
                const status = document.getElementById('status-text');
                try {
                    let res = await fetch(API_URL);
                    let data = await res.json();
                    
                    status.innerText = "● 連線正常 " + new Date().toLocaleTimeString();
                    status.style.color = "#00e676";
                    document.getElementById('spinner').style.display = 'none';

                    ['USD', 'KRW'].forEach(cur => {
                        let rate = data[cur];
                        if(!rate) return;
                        let el = document.getElementById('rate-'+cur);
                        let prev = lastRates[cur];
                        el.innerText = rate;
                        el.className = 'rate ' + (prev && rate > prev ? 'rate-up' : (prev && rate < prev ? 'rate-down' : ''));
                        lastRates[cur] = rate;

                        let c = charts[cur];
                        c.data.labels.push('');
                        c.data.datasets[0].data.push(rate);
                        if(c.data.labels.length > 30) { c.data.labels.shift(); c.data.datasets[0].data.shift(); }
                        c.update();
                        checkAlert(cur, rate);
                    });
                } catch(e) {
                    status.innerText = "連線中斷...";
                    status.style.color = "#ff5252";
                }
            }
            setInterval(update, 10000);
            update();
        </script>
    </body>
    </html>
    """
    return render_template_string(html_content)

# --- 3. API 接口 (資料源) ---
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
