# file: webhook_server.py
from flask import Flask, request
import requests

app = Flask(__name__)
CHANNEL_ACCESS_TOKEN = "Bearer 24+yWuIZvh8f4Zav5giuYlpSZ5j3ZdIF2iPACt+PdF0Wo24kGQUTBgX+wjYWCmn09OKxxzX1HK4za3O5hfHkVYn1oCGZqLE2cXkHxpWMUEH4NK04LLFsBwOUkk1/5KDHAHUOjChCHuwRFEVLU46SZwdB04t89/1O/w1cDnyilFU="
def send_line_message(user_id, message):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "to": user_id,
        "messages": [{"type": "text", "text": message}]
    }
    requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=payload)

@app.route('/webhook', methods=['POST'])
def webhook():
    body = request.json
    print(body)  # เอาไว้ debug
    return "OK"

@app.route('/send-alert', methods=['POST'])
def send_alert():
    data = request.json
    send_line_message(data['user_id'], data['message'])
    return "Alert sent"

if __name__ == '__main__':
    app.run(port=5000)

#nrovtp 