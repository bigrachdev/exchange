# keep_alive.py - Flask-based keep alive server for Render

import os
from flask import Flask
from threading import Thread
import logging

app = Flask('')

@app.route('/')
def home():
    return "🤖 TOPO EXCHANGE Bot is alive and running!"

@app.route('/health')
def health():
    return "OK", 200

@app.route('/status')
def status():
    return {
        "status": "online",
        "bot": "TOPO EXCHANGE",
        "message": "Bot is active and polling"
    }

def run():
    """Run Flask app"""
    import os
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    """Start Flask server in a separate thread"""
    t = Thread(target=run)
    t.daemon = True
    t.start()
    logging.info(f"✅ Keep-alive server started on port {os.environ.get('PORT', 10000)}")