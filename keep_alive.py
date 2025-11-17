# keep_alive.py - UPDATED
from flask import Flask, jsonify
from threading import Thread
import logging
import os
import time

app = Flask('')

@app.route('/')
def home():
    return "🤖 TOPO EXCHANGE Bot - Active ✅"

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "telegram_bot"})

@app.route('/ping')
def ping():
    return "pong"

def run():
    """Run the Flask server"""
    port = int(os.environ.get('PORT', 10000))
    logging.info(f"🌐 Starting keep-alive server on port {port}")
    
    # Simple Flask server - Render handles the production serving
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

def keep_alive():
    """Start the keep-alive server"""
    thread = Thread(target=run, daemon=True)
    thread.start()
    logging.info("✅ Keep-alive server started")