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
            /* --- 全局設定 (Dark Mode) --- */
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
                box-sizing: border-box; /* 讓 padding 不會撐大寬度 */
            }

            /* --- 下拉選單樣式 (仿 iOS 風格) --- */
            .select-container {
                width: 100%;
                max-width: 400px;
                margin-bottom: 20px;
            }
            select {
                width: 100%;
                padding: 12px;
                font-size: 18px;
                border-radius: 12px;
                border: none;
                background-color: #1c1c1e;
                color: white;
                appearance: none; /* 移除預設箭頭 */
                text-align: center;
                font-weight: bold;
                box-shadow: 0 4px 12px rgba(255,255,255,0.1);
                outline: none;
            }

            /* --- 卡片容器 --- */
            .card-wrapper {
                width: 100%;
                max-width: 420px; /* 電腦版最大寬度 */
                display: none; /* 預設隱藏，由 JS 控制顯示 */
                animation: fadeIn 0.5s;
            }
            /* 顯示被選中的卡片 */
            .card-wrapper.active {
                display: block;
            }

            @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

            .card {
                background-color: #1c1c1e;
                border-radius: 20px;
                padding: 25px;
                box-shadow: 0 8px 30px rgba(
